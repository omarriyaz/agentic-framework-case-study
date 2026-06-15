from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.agent import stream_agent
from agent.prompts import HOMEOWNER_ADDENDUM, TECHNICIAN_ADDENDUM

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    remembered_model: str | None = None
    mode: str = "homeowner"

@app.post("/chat")
async def chat(req: ChatRequest):
    message = req.message
    if req.remembered_model:
        message = f"[User's appliance model: {req.remembered_model}]\n{message}"

    mode_addendum = TECHNICIAN_ADDENDUM if req.mode == "technician" else HOMEOWNER_ADDENDUM

    return StreamingResponse(
        stream_agent(message, req.history, mode_addendum),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
