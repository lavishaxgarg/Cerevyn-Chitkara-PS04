import json
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report
from app.classifier import TicketClassifier

root = Path(__file__).resolve().parents[1]
test = json.loads((root / "sample_data" / "test.json").read_text(encoding="utf-8"))
model = TicketClassifier()
actual = [row["category"] for row in test]
predicted = [model.predict(row["message"])[0] for row in test]
print(f"Reserved test examples: {len(test)}")
print(f"Accuracy: {accuracy_score(actual, predicted):.2%}")
print(classification_report(actual, predicted, zero_division=0))
print("Per-example results:")
for row, prediction in zip(test, predicted):
    print(f'{row["ticket_id"]}: expected={row["category"]}, predicted={prediction}, {"PASS" if row["category"] == prediction else "CHECK"}')
