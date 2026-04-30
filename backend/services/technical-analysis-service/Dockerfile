FROM python:3.11-slim
WORKDIR /app
RUN addgroup --system lion && adduser --system --ingroup lion lion
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" "redis[asyncio]" numpy pandas pydantic
COPY services/technical-analysis-service/ .
RUN chown -R lion:lion /app
USER lion
EXPOSE 8005
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
