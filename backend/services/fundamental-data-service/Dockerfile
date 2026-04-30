FROM python:3.11-slim
WORKDIR /app
RUN addgroup --system lion && adduser --system --ingroup lion lion
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" aiohttp "redis[asyncio]" motor pydantic numpy python-dateutil
COPY services/fundamental-data-service/ .
RUN chown -R lion:lion /app
USER lion
EXPOSE 8003
CMD ["python", "-c", "print(''started'')"]
