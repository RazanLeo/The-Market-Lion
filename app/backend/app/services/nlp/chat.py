"""Chat AI — OpenAI primary, Anthropic fallback."""
from __future__ import annotations
import httpx
from ...core.config import settings


SYSTEM_PROMPT = """\
You are the Market Lion AI assistant, embedded inside a professional trading platform.
You analyse markets and explain trading decisions transparently. Reply in the user's preferred language.
Never promise profits. The platform shows historical-only success rates from Backtest+Walk-Forward.
"""


async def generate_response(*, user_id: str, lang: str, message: str, symbol: str | None, tf: str) -> str:
    if settings.OPENAI_API_KEY:
        return await _openai(message, lang)
    if settings.ANTHROPIC_API_KEY:
        return await _anthropic(message, lang)
    return "(LLM provider not configured. Configure OPENAI_API_KEY or ANTHROPIC_API_KEY)"


async def _openai(message: str, lang: str) -> str:
    async with httpx.AsyncClient(timeout=30) as cx:
        r = await cx.post("https://api.openai.com/v1/chat/completions",
                          headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY.get_secret_value()}"},
                          json={
                              "model": "gpt-4o-mini",
                              "messages": [
                                  {"role": "system", "content": SYSTEM_PROMPT + f"\nReply in: {lang}"},
                                  {"role": "user", "content": message},
                              ],
                              "temperature": 0.4,
                          })
        if r.status_code >= 400:
            return f"(LLM error: {r.text[:200]})"
        return r.json()["choices"][0]["message"]["content"]


async def _anthropic(message: str, lang: str) -> str:
    async with httpx.AsyncClient(timeout=30) as cx:
        r = await cx.post("https://api.anthropic.com/v1/messages",
                          headers={
                              "x-api-key": settings.ANTHROPIC_API_KEY.get_secret_value(),
                              "anthropic-version": "2023-06-01",
                              "Content-Type": "application/json",
                          },
                          json={
                              "model": "claude-3-5-haiku-20241022",
                              "system": SYSTEM_PROMPT + f"\nReply in: {lang}",
                              "messages": [{"role": "user", "content": message}],
                              "max_tokens": 1024,
                          })
        if r.status_code >= 400:
            return f"(LLM error: {r.text[:200]})"
        return r.json()["content"][0]["text"]
