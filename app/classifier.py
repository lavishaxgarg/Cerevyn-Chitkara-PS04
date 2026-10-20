"""Small, explainable TF-IDF + Logistic Regression classifier.

Only the 20 examples in sample_data/train.json are used for fitting.
sample_data/test.json is reserved for reporting accuracy and is not imported here.
"""
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent.parent
TRAIN_PATH = ROOT / "sample_data" / "train.json"
CATEGORIES = ["Billing", "Technical", "Access", "General"]

def load_training_data():
    records = json.loads(TRAIN_PATH.read_text(encoding="utf-8"))
    return [r["message"] for r in records], [r["category"] for r in records]

class TicketClassifier:
    def __init__(self):
        texts, labels = load_training_data()
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True)),
            ("model", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
        ])
        self.pipeline.fit(texts, labels)

    def predict(self, message: str):
        probabilities = self.pipeline.predict_proba([message])[0]
        classes = self.pipeline.named_steps["model"].classes_
        ranked = sorted(zip(classes, probabilities), key=lambda item: item[1], reverse=True)
        category, confidence = ranked[0]
        # Low confidence is not silently trusted; it is flagged for human review.
        return category, float(confidence), ranked[:2]
