FROM python:3.11-slim
WORKDIR /app
RUN addgroup --system lion && adduser --system --ingroup lion lion
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" aiohttp "redis[asyncio]" asyncpg numpy pydantic cryptography
COPY services/order_execution_service/ .
RUN chown -R lion:lion /app
USER lion
EXPOSE 8014
CMD ["uvicorn", "executor:app", "--host", "0.0.0.0", "--port", "8014"]
