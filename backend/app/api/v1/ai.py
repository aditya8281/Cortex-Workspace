from fastapi import APIRouter
from backend.app.ai.llm_router import LLMRouter

router = APIRouter()
llm = LLMRouter()

@router.post("/ask")
async def ask(prompt: str):
    response = await llm.generate(prompt)
    return {"response": response}