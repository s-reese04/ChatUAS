import logging
import os
import threading

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag_app import rag

logger = logging.getLogger("chatuas")

app = FastAPI(title="ChatUAS")

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

# Max 2 simultanious requests
slots = threading.BoundedSemaphore(2)


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class Source(BaseModel):
    index: int
    source: str
    page: int | str
    snippet: str


class Answer(BaseModel):
    answer: str
    sources: list[Source]


@app.post("/chat", response_model=Answer)
def chat(q: Question):
    if not slots.acquire(timeout=30):
        raise HTTPException(status_code=503, detail="Der Assistent ist gerade ausgelastet.")
    try:
        return rag(q.question)
    except Exception:
        logger.exception("Fehler in rag()")
        raise HTTPException(status_code=502, detail="Der Assistent ist vorübergehend nicht erreichbar.")
    finally:
        slots.release()


@app.get("/health")
def health():
    return {"ok": True}
