from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.services.rag import answer_question_with_citations

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/ask")
def ask_chatbot(payload: dict, user: User = Depends(get_current_user)) -> dict:
    question = str(payload.get("question", "")).strip()
    if not question:
        return {"answer": "Please ask a question.", "citations": []}
    result = answer_question_with_citations(question)
    return result