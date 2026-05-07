"""Support endpoints — contact form intake.

Sends contact-form submissions to the support inbox via the email service when
configured; otherwise stores them as audit-log entries for manual triage.
"""
from __future__ import annotations

from typing import Annotated
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.logging import get_logger
from ..db.base import get_db
from ..db.models import AuditLog
from ..deps import current_user_optional

router = APIRouter()
log = get_logger("support")


class ContactIn(BaseModel):
    email: EmailStr
    subject: str = Field(min_length=2, max_length=200)
    message: str = Field(min_length=10, max_length=5000)
    locale: str | None = Field(default=None, max_length=8)


@router.post("/contact")
async def contact(
    body: ContactIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user=Depends(current_user_optional),
):
    """Receive a contact-form submission. Persists to audit_log + best-effort email."""
    db.add(AuditLog(
        actor_id=user.id if user else None,
        actor_role="user" if user else "anonymous",
        action="support_contact",
        resource="support",
        meta={"email": body.email, "subject": body.subject,
              "message": body.message, "locale": body.locale,
              "ts": datetime.now(timezone.utc).isoformat()},
    ))
    await db.commit()

    # Best-effort email dispatch
    try:
        from ..services.email.send import send_email  # type: ignore
        to = settings.SUPPORT_EMAIL or "razan.tawfiq@gmail.com"
        await send_email(
            to=to,
            subject=f"[Market Lion] {body.subject}",
            body=f"From: {body.email}\nLocale: {body.locale}\n\n{body.message}",
        )
    except Exception as e:  # pragma: no cover (email service may be off in dev)
        log.info("support_email_skip", err=str(e))

    return {"ok": True, "received_at": datetime.now(timezone.utc).isoformat()}
