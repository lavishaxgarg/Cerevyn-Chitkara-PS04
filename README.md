# Cerevyn Chitkara — PS04 Azure Support Ticket Automation

**Candidate:** Lavisha Rani  
**Roll number:** `REPLACE_WITH_ROLL_NUMBER`  
**Branch:** `REPLACE_WITH_BRANCH`  
**Problem ID:** PS04

> Before submission, replace the roll number and branch placeholders and review every part of the implementation so you can explain and modify it yourself.

## What it does
A local AI-assisted API that classifies fictional support tickets into Billing, Technical, Access, or General; assigns a team; proposes priority; creates a short summary and a draft reply; flags uncertain classifications; stores state in SQLite; rejects duplicate IDs; and requires human approval before a draft becomes `Ready`. It does not send email or contact customers.

## Stack
- Python 3.11, FastAPI, Pydantic
- TF-IDF + Logistic Regression (scikit-learn)
- SQLite
- Pytest, Docker, GitHub Actions
- Azure App Service + Azure Container Registry deployment plan

## Project structure
```text
app/
  main.py             # HTTP API and validation
  service.py          # ticket workflow, priority and approval rules
  classifier.py       # TF-IDF + Logistic Regression
  db.py               # SQLite schema and connection
sample_data/
  train.json          # 20 labelled training examples
  test.json           # 10 held-out evaluation examples
tests/test_api.py     # API and workflow tests
scripts/evaluate.py   # reserved test-set accuracy report
docs/azure-plan.md    # Azure architecture and deployment plan
.github/workflows/
  ci.yml
  deploy-azure.yml
Dockerfile
.env.example
requirements.txt
```

## Run locally (Windows PowerShell or macOS/Linux)
```bash
python -m venv .venv
```
Activate it:
- Windows PowerShell: `.\.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Then:
```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/docs` for interactive API testing and `http://127.0.0.1:8000/health` for the health check.

## Example requests
Create a ticket:
```bash
curl -X POST http://127.0.0.1:8000/tickets \
  -H "Content-Type: application/json" \
  -d "{\"ticket_id\":\"T-1001\",\"message\":\"I was charged twice for my monthly subscription.\"}"
```
Retrieve a ticket:
```bash
curl http://127.0.0.1:8000/tickets/T-1001
```
Approve a draft after human review:
```bash
curl -X POST http://127.0.0.1:8000/tickets/T-1001/approve \
  -H "Content-Type: application/json" \
  -d "{\"approved_by\":\"Support Reviewer\"}"
```
List tickets:
```bash
curl http://127.0.0.1:8000/tickets
```

## Tests and evaluation
```bash
pytest -q
python scripts/evaluate.py
```
The evaluation script reports accuracy on the ten reserved examples. Report the **actual output from your own run** in the submission; do not claim an accuracy value without running it. The held-out set must not be used to tune the classifier.

## Priority policy
- **High:** messages containing explicit urgent-impact indicators such as security breach, account compromised, data leak, production down, fraud, urgent, outage, or charged twice.
- **Medium:** selected access/technical failures that prevent normal use.
- **Low:** other requests.
This is a transparent prototype policy, not an SLA or a substitute for human judgement.

## Uncertainty and approval
The classifier returns its top predicted category and confidence. Low-confidence cases are flagged as `Needs review` and cannot be approved through the normal endpoint until reviewed. Other drafts start as `Pending approval`; the approval endpoint records the reviewer and an audit event. Approval only marks the draft `Ready`; no external message is sent.

## Sample test scenarios
Automated tests cover health, successful ticket creation, duplicate ticket rejection, invalid input, approval of a missing ticket, approval/audit behaviour, and retrieval. Demo additionally:
1. Submit a billing message and inspect the category/priority.
2. Submit an ambiguous message and explain confidence-based review.
3. Submit the same ticket ID twice.
4. Submit a too-short message.
5. Approve a pending draft and inspect its audit log.

## Docker
```bash
docker build -t cerevyn-ps04 .
docker run --rm -p 8000:8000 -v "${PWD}/data:/app/data" cerevyn-ps04
```
Then open `http://127.0.0.1:8000/docs`. In PowerShell, use `${PWD}` as shown or create a local `data` folder first.

## Azure
See [docs/azure-plan.md](docs/azure-plan.md). Live deployment is optional. The manual GitHub Actions workflow uses Azure OIDC references; configure repository secrets/variables and a federated credential before running it.

## Limitations
- Small training dataset; predictions are not production-grade.
- Priority rules are simple keyword rules and should be reviewed by a human.
- The confidence threshold is a heuristic, not a calibrated probability.
- SQLite is intended for local/single-instance demonstration; use a managed database for production/multiple instances.
- No authentication, external email sending, or live LLM API is included.

## Contribution and AI disclosure
- Candidate contribution: `REPLACE_WITH_YOUR_ACTUAL_CONTRIBUTION`.
- AI assistance: `REPLACE_WITH_HONEST_DESCRIPTION_OF_ANY_AI_ASSISTANCE`.
- Reused code: `No third-party application code intentionally copied; dependencies are listed in requirements.txt.` (edit if this is not accurate).

## Final submission checklist
- [ ] Replace roll number, branch, contribution, and AI disclosure placeholders.
- [ ] Run all tests and evaluation locally.
- [ ] Add screenshots and a 3–5 minute demo recording/link.
- [ ] Push to a public GitHub repository or grant reviewer access.
- [ ] Include the final commit hash or release tag in the submission.
