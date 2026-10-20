
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from .service import TicketService
from .db import init_db


service = TicketService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Cerevyn Support Ticket Automation",
    description="AI-assisted ticket triage prototype. Draft responses require human approval.",
    version="1.0.0",
    lifespan=lifespan,
)


class TicketRequest(BaseModel):
    ticket_id: str = Field(
        min_length=2,
        max_length=40,
        pattern=r"^[A-Za-z0-9_-]+$"
    )
    message: str = Field(min_length=8, max_length=2000)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value.strip()


class ApprovalRequest(BaseModel):
    approved_by: str = Field(min_length=2, max_length=80)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets", status_code=201)
def create_ticket(payload: TicketRequest):
    try:
        return service.create_ticket(
            payload.ticket_id,
            payload.message
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    ticket = service.get_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return ticket


@app.post("/tickets/{ticket_id}/approve")
def approve_ticket(ticket_id: str, payload: ApprovalRequest):
    try:
        return service.approve_ticket(
            ticket_id,
            payload.approved_by
        )
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.get("/tickets")
def list_tickets():
    return {"tickets": service.list_tickets()}
