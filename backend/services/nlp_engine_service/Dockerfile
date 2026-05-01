FROM python:3.11-slim
WORKDIR /app
RUN addgroup --system lion && adduser --system --ingroup lion lion
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" aiohttp "redis[asyncio]" motor numpy pydantic python-dateutil
COPY services/nlp_engine_service/ .
RUN chown -R lion:lion /app
USER lion
EXPOSE 8007
CMD ["uvicorn", "nlp_engine:app", "--host", "0.0.0.0", "--port", "8007"]
