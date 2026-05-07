"""Health endpoints — used by Caddy/load-balancers."""
from fastapi import APIRouter
from .. import __version__

router = APIRouter()


@router.get("/healthz")
async def healthz():
    return {"ok": True, "service": "the-market-lion", "version": __version__}


@router.get("/readyz")
async def readyz():
    return {"ok": True}
