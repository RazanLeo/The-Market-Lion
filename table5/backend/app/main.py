# ═══════════════════════════════════════════════════════════════════════════
# 🦁 أسد السوق — FastAPI entrypoint للجدول الخامس
# ═══════════════════════════════════════════════════════════════════════════
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.table_5 import router as table5_router
from app.indicators.registry import verify_total_weight, get_all_71_indicators

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="🦁 The Market Lion — Table 5 (Technical Indicators)",
        description="محرك تصويت الجدول الخامس — 71 مؤشر × 6 أطر زمنية × 10٪ وزن",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def _startup():
        logger.info("🦁 بدء تشغيل الجدول الخامس")
        # تحقق صحة المؤشرات والأوزان
        try:
            verify_total_weight()
            inds = get_all_71_indicators()
            logger.info(f"✅ تم تحميل {len(inds)} مؤشر، إجمالي الأوزان = 10٪")
        except Exception as e:
            logger.exception("❌ فشل تحقق المؤشرات")
            raise

    @app.get("/")
    async def root():
        return {
            "service": "The Market Lion — Table 5",
            "indicators": 71,
            "timeframes": 6,
            "module_weight_pct": 10.0,
            "endpoints": [
                "GET  /api/v1/table-5/meta",
                "GET  /api/v1/table-5/indicators",
                "GET  /api/v1/table-5/decision?symbol=XAU/USD",
                "WS   /api/v1/table-5/ws/{symbol}",
            ],
        }

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    app.include_router(table5_router)
    return app


app = create_app()
