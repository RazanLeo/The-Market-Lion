"""Background price streaming service."""
import asyncio
import logging

logger = logging.getLogger(__name__)


class PriceStreamer:
    def __init__(self):
        self._running = False
        self._task = None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._stream_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _stream_loop(self):
        while self._running:
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Price streamer error: {e}")
                await asyncio.sleep(5)


price_streamer = PriceStreamer()
