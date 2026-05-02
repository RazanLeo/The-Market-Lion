"""Market Lion — Notification Service.
Channels: Telegram Bot, Discord Webhook, Email (SendGrid), Push (FCM), WhatsApp (Twilio).
"""
import asyncio
import os
import logging
import json
import base64
from typing import Optional, List
import aiohttp
import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

logger = logging.getLogger("notifier")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")
SENDGRID_KEY = os.getenv("SENDGRID_API_KEY", "")
FCM_KEY = os.getenv("FCM_SERVER_KEY", "")
TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "")
TWILIO_FROM_WA = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")  # Twilio sandbox
FCM_V1_PROJECT = os.getenv("FCM_PROJECT_ID", "")  # Firebase project ID for v1 API


# ──────────────────────────────────────────────
# Signal message formatter
# ──────────────────────────────────────────────
def format_signal_telegram(signal: dict) -> str:
    side_emoji = "🟢 شراء" if signal.get("side") == "BUY" else "🔴 بيع"
    score = signal.get("confluenceScore", 0)
    score_bar = "▓" * int(score / 10) + "░" * (10 - int(score / 10))
    should = "✅ نعم" if signal.get("shouldTrade") else "⚠️ انتظر"

    return f"""🦁 <b>أسد السوق — إشارة تداول</b>

📊 <b>{signal.get('symbol', '')} | {signal.get('timeframe', '')}</b>
{side_emoji}

📈 <b>التوافق:</b> {score:.1f}% {score_bar}
💰 <b>الدخول:</b> <code>{signal.get('entry', 0):.5f}</code>
🛑 <b>وقف الخسارة:</b> <code>{signal.get('sl', 0):.5f}</code>
🎯 <b>الهدف 1:</b> <code>{signal.get('tp1', 0):.5f}</code> (RR: 1:{signal.get('rr1', 1):.1f})
🎯 <b>الهدف 2:</b> <code>{signal.get('tp2', 0):.5f}</code> (RR: 1:{signal.get('rr2', 2):.1f})
🎯 <b>الهدف 3:</b> <code>{signal.get('tp3', 0):.5f}</code> (RR: 1:{signal.get('rr3', 3):.1f})

📦 <b>حجم الصفقة:</b> {signal.get('lotSize', 0.01)} لوت
⚡️ <b>تنفيذ:</b> {should}

🔍 <b>أبرز المحركات:</b>
{chr(10).join(f"  • {f}" for f in signal.get('topFactors', [])[:5])}

⏰ {signal.get('generatedAt', '')[:19].replace('T', ' ')} UTC

<i>أسد السوق — نظام تداول بالذكاء الاصطناعي</i>"""


def format_signal_discord(signal: dict) -> dict:
    side = signal.get("side", "NEUTRAL")
    color = 0x0E7A2C if side == "BUY" else (0xB0140C if side == "SELL" else 0x888888)
    return {
        "username": "أسد السوق 🦁",
        "embeds": [{
            "title": f"🦁 إشارة — {signal.get('symbol')} {signal.get('timeframe')}",
            "color": color,
            "fields": [
                {"name": "الاتجاه", "value": f"{'🟢 شراء' if side=='BUY' else '🔴 بيع'}", "inline": True},
                {"name": "التوافق", "value": f"{signal.get('confluenceScore', 0):.1f}%", "inline": True},
                {"name": "الدخول", "value": f"`{signal.get('entry', 0):.5f}`", "inline": True},
                {"name": "وقف الخسارة", "value": f"`{signal.get('sl', 0):.5f}`", "inline": True},
                {"name": "TP1", "value": f"`{signal.get('tp1', 0):.5f}`", "inline": True},
                {"name": "TP3", "value": f"`{signal.get('tp3', 0):.5f}`", "inline": True},
            ],
            "footer": {"text": "أسد السوق — The Market Lion"},
            "timestamp": signal.get("generatedAt"),
        }]
    }


# ──────────────────────────────────────────────
# Telegram
# ──────────────────────────────────────────────
async def send_telegram(chat_id: str, message: str) -> bool:
    if not TELEGRAM_TOKEN:
        logger.debug("No Telegram token configured")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        async with aiohttp.ClientSession() as sess:
            resp = await sess.post(url, json=payload)
            return resp.status == 200
    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        return False


async def broadcast_signal_telegram(signal: dict, subscriber_chat_ids: list[str]) -> int:
    message = format_signal_telegram(signal)
    tasks = [send_telegram(cid, message) for cid in subscriber_chat_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return sum(1 for r in results if r is True)


# ──────────────────────────────────────────────
# Discord
# ──────────────────────────────────────────────
async def send_discord(signal: dict) -> bool:
    if not DISCORD_WEBHOOK:
        return False
    payload = format_signal_discord(signal)
    try:
        async with aiohttp.ClientSession() as sess:
            resp = await sess.post(DISCORD_WEBHOOK, json=payload)
            return resp.status in (200, 204)
    except Exception as e:
        logger.error(f"Discord send error: {e}")
        return False


# ──────────────────────────────────────────────
# SendGrid Email
# ──────────────────────────────────────────────
async def send_email(to_email: str, subject: str, html_body: str) -> bool:
    if not SENDGRID_KEY:
        return False
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": "signals@marketlion.ai", "name": "أسد السوق"},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_body}],
    }
    headers = {"Authorization": f"Bearer {SENDGRID_KEY}", "Content-Type": "application/json"}
    try:
        async with aiohttp.ClientSession() as sess:
            resp = await sess.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers)
            return resp.status == 202
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return False


# ──────────────────────────────────────────────
# Firebase Cloud Messaging (Push)
# ──────────────────────────────────────────────
async def send_push(fcm_token: str, title: str, body: str, data: dict = None) -> bool:
    """Firebase Cloud Messaging — legacy HTTP API."""
    if not FCM_KEY:
        return False
    payload = {
        "to": fcm_token,
        "notification": {"title": title, "body": body, "sound": "default", "badge": 1},
        "data": data or {},
        "priority": "high",
    }
    headers = {"Authorization": f"key={FCM_KEY}", "Content-Type": "application/json"}
    try:
        async with aiohttp.ClientSession() as sess:
            resp = await sess.post("https://fcm.googleapis.com/fcm/send", json=payload, headers=headers)
            if resp.status != 200:
                body_text = await resp.text()
                logger.warning(f"FCM response {resp.status}: {body_text[:200]}")
            return resp.status == 200
    except Exception as e:
        logger.error(f"FCM push error: {e}")
        return False


async def send_push_multicast(tokens: List[str], title: str, body: str, data: dict = None) -> int:
    """Send push to multiple FCM tokens, return success count."""
    if not FCM_KEY or not tokens:
        return 0
    payload = {
        "registration_ids": tokens[:500],  # FCM max 500 per request
        "notification": {"title": title, "body": body, "sound": "default"},
        "data": data or {},
        "priority": "high",
    }
    headers = {"Authorization": f"key={FCM_KEY}", "Content-Type": "application/json"}
    try:
        async with aiohttp.ClientSession() as sess:
            resp = await sess.post("https://fcm.googleapis.com/fcm/send", json=payload, headers=headers)
            if resp.status == 200:
                result = await resp.json()
                return result.get("success", 0)
            return 0
    except Exception as e:
        logger.error(f"FCM multicast error: {e}")
        return 0


async def send_whatsapp(to_number: str, message: str) -> bool:
    """Send WhatsApp message via Twilio WhatsApp API."""
    if not TWILIO_SID or not TWILIO_TOKEN:
        return False
    to_wa = f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    auth = base64.b64encode(f"{TWILIO_SID}:{TWILIO_TOKEN}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"}
    form_data = aiohttp.FormData()
    form_data.add_field("From", TWILIO_FROM_WA)
    form_data.add_field("To", to_wa)
    form_data.add_field("Body", message[:1500])
    try:
        async with aiohttp.ClientSession() as sess:
            resp = await sess.post(url, data=form_data, headers={"Authorization": f"Basic {auth}"})
            if resp.status not in (200, 201):
                body_text = await resp.text()
                logger.warning(f"WhatsApp Twilio {resp.status}: {body_text[:200]}")
            return resp.status in (200, 201)
    except Exception as e:
        logger.error(f"WhatsApp error: {e}")
        return False


def format_signal_whatsapp(signal: dict) -> str:
    """WhatsApp-friendly plain text (no HTML tags)."""
    side = "🟢 شراء" if signal.get("side") == "BUY" else "🔴 بيع"
    score = signal.get("confluenceScore", 0)
    return (
        f"🦁 *أسد السوق*\n"
        f"{'─' * 28}\n"
        f"📊 {signal.get('symbol','')} | {signal.get('timeframe','')}\n"
        f"{side} | توافق: {score:.1f}%\n\n"
        f"💰 دخول: {signal.get('entry', 0):.5f}\n"
        f"🛑 SL: {signal.get('sl', 0):.5f}\n"
        f"🎯 TP1: {signal.get('tp1', 0):.5f}\n"
        f"🎯 TP2: {signal.get('tp2', 0):.5f}\n"
        f"🎯 TP3: {signal.get('tp3', 0):.5f}\n\n"
        f"📦 لوت: {signal.get('lotSize', 0.01)} | مخاطرة: {signal.get('riskPct', 2)}%\n"
        f"{'─' * 28}\n"
        f"أسد السوق — Razan AI"
    )


# ──────────────────────────────────────────────
# FastAPI Service
# ──────────────────────────────────────────────
notif_app = FastAPI(title="Notification Service", version="2.0.0")
notif_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_redis_client: Optional[aioredis.Redis] = None


async def _get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/2"), decode_responses=True
        )
    return _redis_client


class SendNotificationRequest(BaseModel):
    channel: str  # telegram | discord | email | push | whatsapp | all
    signal: dict
    targets: Optional[List[str]] = None  # chat_ids / emails / fcm_tokens / phone numbers


class SubscribeRequest(BaseModel):
    user_id: str
    symbol: str
    channels: List[str] = ["telegram"]
    telegram_chat_id: Optional[str] = None
    fcm_token: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None


@notif_app.get("/")
async def root():
    return {"service": "notification-service", "status": "running", "version": "2.0.0"}


@notif_app.get("/health")
async def health():
    return {"status": "healthy"}


@notif_app.get("/metrics")
async def metrics():
    return ""


@notif_app.post("/notify/signal")
async def notify_signal(req: SendNotificationRequest):
    """Send signal notification across one or all channels."""
    signal = req.signal
    channel = req.channel.lower()
    results = {}

    if channel in ("telegram", "all"):
        targets = req.targets or []
        redis = await _get_redis()
        sym = signal.get("symbol", "")
        stored = await redis.smembers(f"telegram_subs:{sym}") if sym else set()
        all_ids = list(set(targets) | stored)
        if all_ids:
            msg = format_signal_telegram(signal)
            sent = await broadcast_signal_telegram(signal, all_ids)
            results["telegram"] = {"sent": sent, "total": len(all_ids)}

    if channel in ("discord", "all"):
        ok = await send_discord(signal)
        results["discord"] = {"sent": ok}

    if channel in ("push", "all") and req.targets:
        sent_count = await send_push_multicast(req.targets, "🦁 إشارة أسد السوق",
                                               f"{signal.get('symbol')} {signal.get('side')} | {signal.get('confluenceScore', 0):.0f}%",
                                               {"type": "signal", "symbol": signal.get("symbol", "")})
        results["push"] = {"sent": sent_count}

    if channel in ("whatsapp", "all") and req.targets:
        msg = format_signal_whatsapp(signal)
        wa_sent = 0
        for number in req.targets:
            ok = await send_whatsapp(number, msg)
            if ok:
                wa_sent += 1
        results["whatsapp"] = {"sent": wa_sent, "total": len(req.targets)}

    return {"status": "dispatched", "results": results}


@notif_app.post("/subscribe")
async def subscribe(req: SubscribeRequest):
    """Register a user's notification preferences for a symbol."""
    redis = await _get_redis()
    pipe = redis.pipeline()

    if req.telegram_chat_id:
        pipe.sadd(f"telegram_subs:{req.symbol}", req.telegram_chat_id)
        pipe.hset(f"user:{req.user_id}:notif", "telegram_chat_id", req.telegram_chat_id)

    if req.fcm_token:
        pipe.sadd(f"fcm_subs:{req.symbol}", req.fcm_token)
        pipe.hset(f"user:{req.user_id}:notif", "fcm_token", req.fcm_token)

    if req.whatsapp_number:
        pipe.sadd(f"wa_subs:{req.symbol}", req.whatsapp_number)
        pipe.hset(f"user:{req.user_id}:notif", "whatsapp", req.whatsapp_number)

    if req.email:
        pipe.sadd(f"email_subs:{req.symbol}", req.email)
        pipe.hset(f"user:{req.user_id}:notif", "email", req.email)

    await pipe.execute()
    return {"status": "subscribed", "symbol": req.symbol, "channels": req.channels}


@notif_app.delete("/subscribe/{user_id}/{symbol}")
async def unsubscribe(user_id: str, symbol: str):
    redis = await _get_redis()
    notif_data = await redis.hgetall(f"user:{user_id}:notif")
    pipe = redis.pipeline()
    if notif_data.get("telegram_chat_id"):
        pipe.srem(f"telegram_subs:{symbol}", notif_data["telegram_chat_id"])
    if notif_data.get("fcm_token"):
        pipe.srem(f"fcm_subs:{symbol}", notif_data["fcm_token"])
    if notif_data.get("whatsapp"):
        pipe.srem(f"wa_subs:{symbol}", notif_data["whatsapp"])
    if notif_data.get("email"):
        pipe.srem(f"email_subs:{symbol}", notif_data["email"])
    await pipe.execute()
    return {"status": "unsubscribed"}


@notif_app.get("/subscribers/{symbol}")
async def get_subscribers(symbol: str):
    redis = await _get_redis()
    return {
        "symbol": symbol,
        "telegram": len(await redis.smembers(f"telegram_subs:{symbol}")),
        "push": len(await redis.smembers(f"fcm_subs:{symbol}")),
        "whatsapp": len(await redis.smembers(f"wa_subs:{symbol}")),
        "email": len(await redis.smembers(f"email_subs:{symbol}")),
    }


@notif_app.get("/log")
async def get_notification_log(limit: int = 50):
    redis = await _get_redis()
    items = await redis.lrange("notification_log", 0, min(limit, 200) - 1)
    return {"log": [json.loads(i) for i in items]}


# ──────────────────────────────────────────────
# Background Worker (Redis queue)
# ──────────────────────────────────────────────
class NotificationWorker:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def init(self):
        self._redis = await aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/2"), decode_responses=True
        )

    async def _get_symbol_subs(self, symbol: str, channel: str) -> list:
        key = {"telegram": "telegram_subs", "push": "fcm_subs", "whatsapp": "wa_subs", "email": "email_subs"}.get(channel, "telegram_subs")
        return list(await self._redis.smembers(f"{key}:{symbol}"))

    async def process_signal(self, signal: dict):
        symbol = signal.get("symbol", "")
        should_trade = signal.get("shouldTrade", False)
        if not should_trade:
            return

        # All channels in parallel
        tasks = []

        # Telegram
        tg_ids = await self._get_symbol_subs(symbol, "telegram")
        if tg_ids:
            tasks.append(broadcast_signal_telegram(signal, tg_ids))

        # Discord
        tasks.append(send_discord(signal))

        # Push (FCM)
        fcm_tokens = await self._get_symbol_subs(symbol, "push")
        if fcm_tokens:
            title = "🦁 إشارة أسد السوق"
            body_txt = f"{symbol} {signal.get('side')} | توافق {signal.get('confluenceScore',0):.0f}%"
            tasks.append(send_push_multicast(fcm_tokens, title, body_txt,
                                              {"type": "signal", "symbol": symbol, "side": signal.get("side")}))

        # WhatsApp
        wa_numbers = await self._get_symbol_subs(symbol, "whatsapp")
        wa_msg = format_signal_whatsapp(signal)
        for number in wa_numbers[:20]:  # cap for rate limiting
            tasks.append(send_whatsapp(number, wa_msg))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Notifications dispatched for {symbol}: {len(tasks)} tasks")

        await self._redis.lpush(
            "notification_log",
            json.dumps({
                "signal_symbol": symbol, "side": signal.get("side"),
                "confluenceScore": signal.get("confluenceScore"),
                "telegram_subs": len(tg_ids), "wa_subs": len(wa_numbers),
                "push_subs": len(fcm_tokens),
                "ts": signal.get("generatedAt"),
            })
        )
        await self._redis.ltrim("notification_log", 0, 999)

    async def run(self):
        await self.init()
        logger.info("Notification worker ready — all channels active")
        while True:
            try:
                item = await self._redis.brpop("signal_queue", timeout=5)
                if item:
                    _, raw = item
                    signal = json.loads(raw)
                    await self.process_signal(signal)
            except Exception as e:
                logger.error(f"Notification worker error: {e}")
                await asyncio.sleep(1)


@notif_app.on_event("startup")
async def startup_worker():
    worker = NotificationWorker()
    asyncio.create_task(worker.run())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("notifier:notif_app", host="0.0.0.0", port=8014, reload=True)
