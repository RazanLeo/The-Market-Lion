FROM python:3.11-slim
WORKDIR /app
RUN addgroup --system lion && adduser --system --ingroup lion lion
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" aiohttp "redis[asyncio]" asyncpg numpy pandas websockets python-dateutil yfinance
COPY services/market_data_service/ .
RUN chown -R lion:lion /app
USER lion
EXPOSE 8004
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
