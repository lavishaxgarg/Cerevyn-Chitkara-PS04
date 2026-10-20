import os
import tempfile
from pathlib import Path

# Set a unique temporary database before importing app modules.
_tmp = tempfile.NamedTemporaryFile(delete=False)
_tmp.close()
os.environ["DATABASE_PATH"] = _tmp.name

from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db

init_db()
client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_ticket_and_fields():
    response = client.post("/tickets", json={
        "ticket_id": "TEST-1001",
        "message": "I was charged twice for my subscription and need help."
    })
    assert response.status_code == 201
    body = response.json()
    assert body["category"] in {"Billing", "Technical", "Access", "General"}
    assert body["priority"] in {"Low", "Medium", "High"}
    assert body["assigned_team"]
    assert body["draft_response"]
    assert body["status"] in {"Pending approval", "Needs review"}

def test_duplicate_ticket_id_rejected():
    payload = {"ticket_id": "DUP-1001", "message": "Please explain the fee on my invoice."}
    assert client.post("/tickets", json=payload).status_code == 201
    response = client.post("/tickets", json=payload)
    assert response.status_code == 409
    assert "Duplicate" in response.json()["detail"]

def test_invalid_short_message_rejected():
    response = client.post("/tickets", json={"ticket_id": "BAD-1001", "message": "hi"})
    assert response.status_code == 422

def test_approval_requires_existing_ticket():
    response = client.post("/tickets/NO-SUCH/approve", json={"approved_by": "Reviewer"})
    assert response.status_code == 404

def test_approval_updates_state_and_audit():
    created = client.post("/tickets", json={
        "ticket_id": "APPROVE-1001",
        "message": "Please send me a copy of my payment receipt."
    })
    assert created.status_code == 201
    body = created.json()
    if body["needs_review"]:
        # Low-confidence tickets must not be approved automatically.
        response = client.post("/tickets/APPROVE-1001/approve", json={"approved_by": "Reviewer"})
        assert response.status_code == 409
    else:
        response = client.post("/tickets/APPROVE-1001/approve", json={"approved_by": "Reviewer"})
        assert response.status_code == 200
        assert response.json()["status"] == "Ready"
        assert response.json()["approved_by"] == "Reviewer"
        assert any(row["action"] == "APPROVED" for row in response.json()["audit_log"])

def test_ticket_can_be_retrieved():
    created = client.post("/tickets", json={
        "ticket_id": "GET-1001",
        "message": "The app crashes whenever I open the dashboard."
    })
    assert created.status_code == 201
    response = client.get("/tickets/GET-1001")
    assert response.status_code == 200
    assert response.json()["ticket_id"] == "GET-1001"
