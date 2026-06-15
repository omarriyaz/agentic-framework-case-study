from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent import run_agent
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
    mode: str = "homeowner"  # "homeowner" | "technician"

@app.post("/chat")
async def chat(req: ChatRequest):
    message = req.message
    if req.remembered_model:
        message = f"[User's appliance model: {req.remembered_model}]\n{message}"
    mode_addendum = TECHNICIAN_ADDENDUM if req.mode == "technician" else HOMEOWNER_ADDENDUM
    response, parts, chips, detected_model = await run_agent(message, req.history, mode_addendum)
    return {
        "response": response,
        "parts": parts,
        "chips": chips,
        "detected_model": detected_model,
    }