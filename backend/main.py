"""FastAPI routes only. Logic lives in sessions.py and model_client.py."""

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import db
import sessions

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Mental Health Skills Prototype", lifespan=lifespan)

# The Vite dev server proxies /api to this app, so the browser normally sees
# one origin. CORS is kept for direct access during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class SessionStart(BaseModel):
    client_id: str = Field(min_length=1, max_length=64)
    skill: str = Field(min_length=1, max_length=32)
    entry_choice: str | None = Field(default=None, max_length=64)
    setup_ms: int | None = Field(default=None, ge=0)
    planned_ms: int | None = Field(default=None, ge=0)
    steps_planned: int | None = Field(default=None, ge=0)
    started_at: str | None = Field(default=None, max_length=40)


class SessionEnd(BaseModel):
    end_reason: str
    measured_ms: int | None = Field(default=None, ge=0)
    pauses_ms: int | None = Field(default=None, ge=0)
    crisis_ms: int | None = Field(default=None, ge=0)
    steps_completed: int | None = Field(default=None, ge=0)


class FeedbackIn(BaseModel):
    rating: str


class TextIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/sessions")
def start_session(payload: SessionStart):
    return sessions.create_session(**payload.model_dump())


@app.post("/api/sessions/{client_id}/end")
async def end_session(client_id: str, request: Request):
    # navigator.sendBeacon sends text/plain, so parse the body by hand
    # instead of relying on the JSON content type.
    try:
        payload = SessionEnd(**json.loads(await request.body() or b"{}"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid end payload")
    try:
        # sqlite3 is blocking; keep it off the event loop in this async route.
        row = await run_in_threadpool(sessions.end_session, client_id, **payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if row is None:
        raise HTTPException(status_code=404, detail="Unknown session")
    return row


@app.post("/api/sessions/{client_id}/acknowledgment")
def acknowledgment(client_id: str):
    try:
        return sessions.acknowledge_session(client_id)
    except sessions.SessionNotFound:
        raise HTTPException(status_code=404, detail="Unknown session")
    except sessions.SessionStopped:
        raise HTTPException(status_code=409, detail="Session was stopped")


@app.post("/api/sessions/{client_id}/messages")
def message(client_id: str, payload: TextIn):
    try:
        return sessions.submit_text(client_id, payload.text)
    except sessions.SessionNotFound:
        raise HTTPException(status_code=404, detail="Unknown session")
    except sessions.SessionStopped:
        raise HTTPException(status_code=409, detail="Session was stopped")


@app.post("/api/sessions/{client_id}/feedback")
def feedback(client_id: str, payload: FeedbackIn):
    try:
        found = sessions.set_feedback(client_id, payload.rating)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not found:
        raise HTTPException(status_code=404, detail="Unknown session")
    return {"saved": True}


@app.get("/api/history")
def history():
    return {"sessions": sessions.get_history()}


@app.get("/api/usual")
def usual():
    return {"skill": sessions.get_usual_skill()}
