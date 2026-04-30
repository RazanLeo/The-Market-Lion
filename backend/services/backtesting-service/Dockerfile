FROM python:3.11-slim
WORKDIR /app
RUN addgroup --system lion && adduser --system --ingroup lion lion
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" asyncpg "redis[asyncio]" numpy pandas pydantic aiohttp python-dateutil
COPY services/backtesting-service/ .
RUN chown -R lion:lion /app
USER lion
EXPOSE 8002
CMD ["uvicorn", "backtester:bt_app", "--host", "0.0.0.0", "--port", "8002"]
