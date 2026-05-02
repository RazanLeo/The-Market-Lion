"""AI Chat router — محلل أسد السوق (The Market Lion Analyst)."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user
from models.user import User
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """أنت محلل أسد السوق — مستشار مالي متخصص بالتداول الآلي وتحليل الأسواق المالية.

قواعد التواصل:
- الرد بالعربية دائماً ما لم يتحدث المستخدم بالإنجليزية
- تقديم نفسك كـ"محلل أسد السوق" وليس كـ"بوت"
- لا تضمن أرباحاً ولا تشجع على المخاطرة العالية
- استخدم أرقاماً وإحصائيات عند الإمكان
- كن محترفاً ومختصراً ودقيقاً
- إذا سُئلت عن صفقة، قدم: الاتجاه، نقطة الدخول، وقف الخسارة، والأهداف
- ذكّر دائماً أن التداول ينطوي على مخاطر وأن هذا ليس نصيحة استثمارية

تخصصاتك:
- تحليل الذهب (XAU/USD) — الأصل الأهم في المنصة
- تحليل النفط والفوركس والعملات المشفرة
- مدارس التحليل الفني: SMC, ICT, Wyckoff, Elliott Wave, Fibonacci, Price Action
- قراءة Order Blocks و Fair Value Gaps والسيولة (Liquidity)
- إدارة المخاطر وحماية رأس المال
- تفسير مؤشرات: RSI, MACD, EMA, Bollinger, Ichimoku, ADX, Stochastic
- التحليل الأساسي: تأثير الفيدرالي، ECB، أوبك+ على الأسعار
- قراءة مستويات الدعم والمقاومة
- نظرية داو وأنماط الشموع اليابانية

المنصة:
- اسمها "أسد السوق / Market Lion"
- تدعم: XAU/USD, XAG/USD, WTI, Brent, EUR/USD, GBP/USD, USD/JPY, BTC/USD, ETH/USD وغيرها
- تعمل مع: Capital.com, Exness, MT5
- نماذج الاشتراك: مجاني، Pro (2000 ريال/شهر)، VIP (6000 ريال/شهر)"""


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    context: Optional[dict] = None  # e.g. {"symbol": "XAU/USD", "analysis": {...}}


# ── Canned responses (Arabic-first) for when OpenAI is not available ─────────

CANNED_RESPONSES: dict[str, str] = {
    "gold": (
        "الذهب (XAU/USD) هو الأصل الأهم في استراتيجية أسد السوق. "
        "يتأثر بشكل رئيسي بـ:\n"
        "• العوائد الحقيقية الأمريكية (TIPS) — علاقة عكسية\n"
        "• مؤشر الدولار (DXY) — علاقة عكسية\n"
        "• قرارات الفيدرالي — رفع الفائدة يضغط على الذهب\n"
        "• الجيوسياسة والتضخم — يرفعان الطلب\n\n"
        "عند البحث عن إشارة دخول، ابحث عن:\n"
        "1. تقاطع إيجابي لـ MACD\n"
        "2. RSI يرتد من منطقة 30-40\n"
        "3. الدعم على EMA 50 أو EMA 200\n"
        "4. نمط شمعاني قوي (مطرقة / ابتلاع صعودي)"
    ),
    "signal": (
        "لرؤية إشارات البوت اللحظية:\n"
        "1. توجه للوحة التحكم > التحليل الفني\n"
        "2. اختر الرمز والإطار الزمني\n"
        "3. ستجد درجة التوافق (Confluence Score) والإشارة الحالية\n"
        "4. كل إشارة تتضمن: Entry / SL / TP1 / TP2 / TP3\n\n"
        "الإشارة تُفعَّل عندما يتجاوز التوافق 75% عبر 10 مدارس تحليلية."
    ),
    "risk": (
        "إدارة المخاطر في أسد السوق تعتمد على 5 طبقات:\n"
        "1. SL بحد أدنى 1.5×ATR\n"
        "2. نسبة مخاطرة/عائد: 1:1.5 كحد أدنى (نستهدف 1:3)\n"
        "3. حد 1-2% مخاطرة لكل صفقة من رأس المال\n"
        "4. Circuit Breaker: توقف تلقائي عند DD > 3% يومي\n"
        "5. News Shield: تجنب الدخول قبل الأخبار عالية التأثير بـ 30 دقيقة"
    ),
    "eurusd": (
        "EUR/USD — الزوج الأكثر سيولة في الفوركس:\n"
        "• يتأثر بقرارات البنك الأوروبي (ECB) مقابل الاحتياطي الفيدرالي\n"
        "• أهم المستويات: 1.0800 دعم قوي، 1.1000 مقاومة نفسية\n"
        "• أفضل وقت للتداول: فتح لندن (07:00-10:00 GMT) وفتح نيويورك (12:00-15:00 GMT)\n"
        "• المؤشرات الأكثر تأثيراً: NFP, CPI, GDP للولايات المتحدة وأوروبا"
    ),
    "bitcoin": (
        "BTC/USD — ملك العملات المشفرة:\n"
        "• دورة النصفة (Halving) أبريل 2024 — تأثير تاريخي إيجابي للـ 12-18 شهر اللاحقة\n"
        "• المستويات الرئيسية: 60,000$ دعم قوي، 70,000$ مقاومة نفسية\n"
        "• التداول الأسبوعي وراء 60% من التذبذب\n"
        "• تابع صافي تدفق ETF البيتكوين للحكم على الطلب المؤسسي"
    ),
    "subscribe": (
        "باقات أسد السوق:\n\n"
        "• مجاني: إشارات يدوية، رسوم بيانية أساسية\n"
        "• Pro (2,000 ريال/شهر): تداول آلي، كل الرموز، ربط البروكر، تحليل كامل\n"
        "• VIP (6,000 ريال/شهر): كل Pro + متتبع الحيتان + دعم مخصص + تقارير مخصصة\n\n"
        "للاشتراك توجه إلى: الإعدادات > الاشتراك"
    ),
    "smc": (
        "مفهوم الأموال الذكية (SMC - Smart Money Concepts):\n\n"
        "الأدوات الأساسية:\n"
        "• Order Block (OB): آخر شمعة عكسية قبل حركة قوية — منطقة احتمالية لإعادة الاختبار\n"
        "• Fair Value Gap (FVG): فجوة بين 3 شموع — الأسعار تميل لملئها\n"
        "• Liquidity: مناطق تجمع وقف الخسارة (أعلى القمم / أسفل القيعان)\n"
        "• Change of Character (ChoCh): أول مؤشر على تغيير الاتجاه\n"
        "• Break of Structure (BOS): تأكيد الاتجاه الجديد\n\n"
        "الهدف: التداول مع مؤسسات السوق وليس ضدها."
    ),
    "help": (
        "أنا محلل أسد السوق، يمكنني مساعدتك في:\n\n"
        "📊 التحليل الفني:\n"
        "• تحليل أي رمز (اكتب مثلاً: 'حلل الذهب')\n"
        "• شرح أي مؤشر أو مدرسة تحليلية\n\n"
        "📰 التحليل الأساسي:\n"
        "• تأثير الأحداث الاقتصادية على الأسواق\n\n"
        "⚙️ إعدادات البوت:\n"
        "• مساعدتك في ضبط البوت وإدارة المخاطر\n\n"
        "أكتب سؤالك وسأساعدك!"
    ),
    "default": (
        "مرحباً! أنا محلل أسد السوق 🦁\n"
        "يمكنني مساعدتك في تحليل الأسواق وفهم الإشارات وشرح استراتيجيات التداول.\n\n"
        "جرب أن تسألني عن:\n"
        "• تحليل رمز معين (الذهب، اليورو/دولار، البيتكوين...)\n"
        "• شرح مفهوم تقني (SMC، فيبوناتشي، موجات إليوت...)\n"
        "• إدارة المخاطر والرسملة\n"
        "• باقات الاشتراك\n\n"
        "كيف يمكنني مساعدتك اليوم؟"
    ),
}

# Keyword → response key mapping
KEYWORD_MAP = {
    "ذهب": "gold", "gold": "gold", "xauusd": "gold", "xau": "gold",
    "إشارة": "signal", "إشارات": "signal", "signal": "signal", "signals": "signal",
    "مخاطر": "risk", "خطر": "risk", "risk": "risk", "sl": "risk", "stop loss": "risk",
    "يورو": "eurusd", "eur": "eurusd", "eurusd": "eurusd",
    "بيتكوين": "bitcoin", "bitcoin": "bitcoin", "btc": "bitcoin", "btcusd": "bitcoin",
    "اشتراك": "subscribe", "باقة": "subscribe", "subscribe": "subscribe", "plan": "subscribe",
    "smc": "smc", "أموال ذكية": "smc", "smart money": "smc", "order block": "smc",
    "مساعدة": "help", "help": "help", "?": "help",
}


def _find_canned_response(message: str) -> str:
    msg_lower = message.lower().strip()
    for keyword, response_key in KEYWORD_MAP.items():
        if keyword in msg_lower:
            return CANNED_RESPONSES[response_key]
    return CANNED_RESPONSES["default"]


def _build_context_note(context: Optional[dict]) -> str:
    if not context:
        return ""
    parts = []
    if symbol := context.get("symbol"):
        parts.append(f"الرمز المعروض: {symbol}")
    if analysis := context.get("analysis"):
        if signal := analysis.get("signal"):
            parts.append(f"الإشارة الحالية: {signal.upper()}")
        if score := analysis.get("confluence_score"):
            parts.append(f"درجة التوافق: {score:.0%}")
        if price := analysis.get("price"):
            parts.append(f"السعر الحالي: {price}")
        if trend := analysis.get("trend"):
            trend_ar = {"bullish": "صاعد", "bearish": "هابط", "neutral": "محايد"}.get(trend, trend)
            parts.append(f"الاتجاه: {trend_ar}")
    return "السياق: " + " | ".join(parts) if parts else ""


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Chat with the Market Lion AI analyst."""
    # Try OpenAI if key is available
    if settings.OPENAI_API_KEY:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            # Add context if provided
            context_note = _build_context_note(req.context)
            if context_note:
                messages.append({"role": "system", "content": context_note})

            # Add conversation history (last 10 messages)
            for h in req.history[-10:]:
                if h.role in ("user", "assistant"):
                    messages.append({"role": h.role, "content": h.content})

            messages.append({"role": "user", "content": req.message})

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=600,
                temperature=0.7,
            )
            reply = response.choices[0].message.content or ""
            return {
                "reply": reply,
                "source": "openai",
                "model": "gpt-4o-mini",
            }
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}")

    # Fallback: intelligent canned responses
    reply = _find_canned_response(req.message)
    return {
        "reply": reply,
        "source": "local",
        "note": "OpenAI API key not configured — using built-in responses",
    }
