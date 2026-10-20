from datetime import datetime, timezone
from .db import get_connection
from .classifier import TicketClassifier

TEAM_BY_CATEGORY = {
    "Billing": "Finance Support",
    "Technical": "Technical Support",
    "Access": "Identity & Access Support",
    "General": "Customer Care",
}

DRAFTS = {
    "Billing": "Thanks for contacting us about a billing concern. Our Finance Support team will review the details. Please do not share full payment-card details in this ticket.",
    "Technical": "Thanks for reporting this technical issue. Our Technical Support team will investigate. If possible, share the steps to reproduce the issue and any non-sensitive error message.",
    "Access": "Thanks for contacting us about account access. Our Identity & Access Support team will review your request. Never send your password or one-time verification code.",
    "General": "Thanks for contacting support. Our Customer Care team will review your question and follow up with the next steps.",
}

URGENT_TERMS = ("security breach", "account compromised", "data leak", "cannot access", "production down", "all users affected", "fraud")
HIGH_TERMS = ("urgent", "asap", "blocked", "outage", "failed payment", "charged twice", "locked out")

def choose_priority(message: str, category: str) -> str:
    text = message.lower()
    if any(term in text for term in URGENT_TERMS):
        return "High"
    if any(term in text for term in HIGH_TERMS):
        return "High"
    if category in ("Access", "Technical") and any(word in text for word in ("cannot", "can't", "unable", "not working")):
        return "Medium"
    return "Low"

def make_summary(message: str) -> str:
    clean = " ".join(message.split())
    words = clean.split()
    if len(words) <= 18:
        return clean
    return " ".join(words[:18]) + "…"

class TicketService:
    def __init__(self):
        self.classifier = TicketClassifier()

    def create_ticket(self, ticket_id: str, message: str):
        category, confidence, _ = self.classifier.predict(message)
        priority = choose_priority(message, category)
        needs_review = confidence < 0.42
        status = "Needs review" if needs_review else "Pending approval"
        summary = make_summary(message)
        with get_connection() as conn:
            if conn.execute("SELECT 1 FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone():
                raise ValueError(f"Duplicate ticket ID: {ticket_id}")
            conn.execute("""
                INSERT INTO tickets
                (ticket_id, message, category, priority, assigned_team, summary, draft_response,
                 confidence, needs_review, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ticket_id, message, category, priority, TEAM_BY_CATEGORY[category], summary,
                  DRAFTS[category], confidence, int(needs_review), status))
            conn.execute(
                "INSERT INTO audit_log(ticket_id, action, actor, details) VALUES (?, ?, ?, ?)",
                (ticket_id, "CREATED", "system", f"category={category}; priority={priority}; confidence={confidence:.3f}")
            )
        return self.get_ticket(ticket_id)

    def get_ticket(self, ticket_id: str):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["needs_review"] = bool(result["needs_review"])
            result["audit_log"] = [dict(item) for item in conn.execute(
                "SELECT action, actor, details, created_at FROM audit_log WHERE ticket_id = ? ORDER BY id",
                (ticket_id,)
            ).fetchall()]
            return result

    def list_tickets(self):
        with get_connection() as conn:
            rows = conn.execute("SELECT ticket_id, category, priority, assigned_team, status, confidence, needs_review, created_at FROM tickets ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]

    def approve_ticket(self, ticket_id: str, approved_by: str):
        with get_connection() as conn:
            row = conn.execute("SELECT status, needs_review FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
            if row is None:
                raise LookupError(ticket_id)
            if row["status"] == "Ready":
                raise ValueError("Ticket draft has already been approved")
            if row["needs_review"]:
                raise ValueError("Ticket is flagged for review; resolve the classification before approval")
            now = datetime.now(timezone.utc).isoformat()
            conn.execute("UPDATE tickets SET status = 'Ready', approved_by = ?, approved_at = ? WHERE ticket_id = ?",
                         (approved_by.strip(), now, ticket_id))
            conn.execute("INSERT INTO audit_log(ticket_id, action, actor, details) VALUES (?, ?, ?, ?)",
                         (ticket_id, "APPROVED", approved_by.strip(), "Draft marked ready; no message was sent"))
        return self.get_ticket(ticket_id)
