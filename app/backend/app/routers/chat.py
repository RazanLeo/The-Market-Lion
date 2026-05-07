"""Embedded financial AI chat (GPT-4o-mini default with fallback)."""
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import current_user
from ..db.base import get_db
from ..db.models import User
from ..services.nlp.chat import generate_response

router = APIRouter()


class ChatIn(BaseModel):
    message: str
    context_symbol: str | None = None
    context_tf: str | None = "15M"


@router.post("")
async def chat(body: ChatIn, user: Annotated[User, Depends(current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    text = await generate_response(user_id=str(user.id), lang=user.preferred_lang, message=body.message, symbol=body.context_symbol, tf=body.context_tf or "15M")
    return {"ok": True, "reply": text}
