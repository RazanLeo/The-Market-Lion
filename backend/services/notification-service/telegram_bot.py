"""Market Lion — Telegram Bot.
Commands: /start, /signal [symbol] [tf], /subscribe, /unsubscribe, /performance, /help
"""
import asyncio
import os
import logging
import json
from typing import Optional
import aiohttp
import redis.asyncio as aioredis

logger = logging.getLogger("telegram-bot")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


# ──────────────────────────────────────────────
# Telegram API helpers
# ──────────────────────────────────────────────
async def call_api(method: str, payload: dict) -> Optional[dict]:
    if not TOKEN:
        return None
    url = f"{BASE_URL}/{method}"
    async with aiohttp.ClientSession() as sess:
        resp = await sess.post(url, json=payload)
        if resp.status == 200:
            return await resp.json()
    return None


async def send_message(chat_id: int | str, text: str, parse_mode: str = "HTML") -> bool:
    result = await call_api("sendMessage", {
        "chat_id": chat_id, "text": text,
        "parse_mode": parse_mode, "disable_web_page_preview": True
    })
    return bool(result and result.get("ok"))


async def get_updates(offset: int = 0) -> list[dict]:
    result = await call_api("getUpdates", {"offset": offset, "timeout": 30, "limit": 100})
    if result and result.get("ok"):
        return result.get("result", [])
    return []


# ──────────────────────────────────────────────
# Command handlers
# ──────────────────────────────────────────────
HELP_TEXT = """🦁 <b>أسد السوق — أوامر البوت</b>

/signal [رمز] [إطار] — احصل على إشارة
  مثال: /signal XAUUSD H1

/subscribe [رمز] — اشترك في إشارات رمز
  مثال: /subscribe XAUUSD

/unsubscribe [رمز] — إلغاء الاشتراك

/performance — إحصاءات الأداء

/symbols — قائمة الرموز المتاحة

/help — عرض هذه المساعدة

━━━━━━━━━━━━━━━
<i>الباقة الاحترافية أو فأعلى مطلوبة للوصول الكامل</i>"""

SYMBOLS_TEXT = """📊 <b>الرموز المتاحة</b>

🥇 <b>معادن:</b> XAUUSD · XAGUSD
🛢️ <b>طاقة:</b> USOIL · XBRUSD
💱 <b>فوركس رئيسي:</b>
  EURUSD · GBPUSD · USDJPY
  AUDUSD · USDCHF · USDCAD
  NZDUSD
💱 <b>فوركس ثانوي:</b>
  EURGBP · EURJPY · GBPJPY
  EURAUD · GBPAUD
🪙 <b>كريبتو:</b> BTCUSD · ETHUSD · SOLUSD

<i>استخدم الرمز بدون / في الأوامر</i>"""


async def handle_start(chat_id: int, user_name: str):
    text = f"""مرحباً <b>{user_name}</b> في 🦁 <b>أسد السوق</b>!

نظام التداول الذكي المتكامل — 65+ مدرسة تحليل فني + أساسي.

استخدم /help لعرض الأوامر المتاحة.
استخدم /signal XAUUSD H1 للحصول على إشارة ذهب.

<i>للحصول على الباقة الاحترافية: marketlion.ai/pricing</i>"""
    await send_message(chat_id, text)


async def handle_help(chat_id: int):
    await send_message(chat_id, HELP_TEXT)


async def handle_symbols(chat_id: int):
    await send_message(chat_id, SYMBOLS_TEXT)


async def handle_signal(chat_id: int, symbol: str, timeframe: str, redis: aioredis.Redis):
    symbol = symbol.upper()
    timeframe = timeframe.upper()
    await send_message(chat_id, f"⏳ جاري توليد إشارة {symbol} {timeframe}...")

    # Check Redis cache first
    cache_key = f"signal:{symbol}:{timeframe}"
    cached = await redis.get(cache_key)
    if cached:
        signal = json.loads(cached)
        from notifier import format_signal_telegram
        await send_message(chat_id, format_signal_telegram(signal))
        return

    # Fetch from API
    api_url = os.getenv("API_URL", "http://gateway:8000")
    try:
        async with aiohttp.ClientSession() as sess:
            resp = await sess.get(f"{api_url}/api/v1/signal/{symbol}/{timeframe}", timeout=aiohttp.ClientTimeout(total=30))
            if resp.status == 200:
                signal = await resp.json()
                from notifier import format_signal_telegram
                await send_message(chat_id, format_signal_telegram(signal))
                return
    except Exception as e:
        logger.error(f"Signal fetch error: {e}")

    await send_message(chat_id, f"❌ تعذر توليد إشارة {symbol} — حاول مرة أخرى لاحقاً")


async def handle_subscribe(chat_id: int, symbol: str, redis: aioredis.Redis):
    symbol = symbol.upper()
    sub_key = f"telegram_subs:{symbol}"
    await redis.sadd(sub_key, str(chat_id))
    await send_message(chat_id, f"✅ تم الاشتراك في إشارات <b>{symbol}</b>\nستصلك الإشارات تلقائياً عند توليدها.")


async def handle_unsubscribe(chat_id: int, symbol: str, redis: aioredis.Redis):
    symbol = symbol.upper()
    sub_key = f"telegram_subs:{symbol}"
    await redis.srem(sub_key, str(chat_id))
    await send_message(chat_id, f"✅ تم إلغاء اشتراك <b>{symbol}</b>")


async def handle_performance(chat_id: int):
    text = """📈 <b>إحصاءات الأداء (آخر 30 يوم)</b>

🎯 <b>نسبة الفوز:</b> 78.4%
💰 <b>صافي الربح:</b> +$3,840
📊 <b>Sharpe Ratio:</b> 2.8
📉 <b>Max Drawdown:</b> 8.2%
🔢 <b>عدد الصفقات:</b> 47
⚡️ <b>Profit Factor:</b> 3.2

<i>البيانات تجريبية — للإحصاءات الحقيقية سجل دخولك</i>"""
    await send_message(chat_id, text)


# ──────────────────────────────────────────────
# Main polling loop
# ──────────────────────────────────────────────
class TelegramBot:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._offset = 0

    async def init(self):
        self._redis = await aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/2"), decode_responses=True
        )

    async def process_update(self, update: dict):
        message = update.get("message") or update.get("edited_message")
        if not message:
            return

        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()
        user_name = message.get("from", {}).get("first_name", "صديقي")

        if not text.startswith("/"):
            return

        parts = text.split()
        command = parts[0].lower().split("@")[0]  # remove bot username

        if command == "/start":
            await handle_start(chat_id, user_name)
        elif command == "/help":
            await handle_help(chat_id)
        elif command == "/symbols":
            await handle_symbols(chat_id)
        elif command == "/performance":
            await handle_performance(chat_id)
        elif command == "/signal":
            symbol = parts[1] if len(parts) > 1 else "XAUUSD"
            tf = parts[2] if len(parts) > 2 else "H1"
            await handle_signal(chat_id, symbol, tf, self._redis)
        elif command == "/subscribe":
            symbol = parts[1] if len(parts) > 1 else "XAUUSD"
            await handle_subscribe(chat_id, symbol, self._redis)
        elif command == "/unsubscribe":
            symbol = parts[1] if len(parts) > 1 else "XAUUSD"
            await handle_unsubscribe(chat_id, symbol, self._redis)
        else:
            await send_message(chat_id, "❓ أمر غير معروف — استخدم /help")

    async def run(self):
        await self.init()
        if not TOKEN:
            logger.warning("No TELEGRAM_BOT_TOKEN set — bot not running")
            return

        logger.info("Telegram bot started polling...")
        while True:
            try:
                updates = await get_updates(self._offset)
                for update in updates:
                    await self.process_update(update)
                    self._offset = update["update_id"] + 1
            except Exception as e:
                logger.error(f"Bot polling error: {e}")
                await asyncio.sleep(5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot = TelegramBot()
    asyncio.run(bot.run())
