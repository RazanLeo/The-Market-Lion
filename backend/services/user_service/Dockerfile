FROM python:3.11-slim
WORKDIR /app
RUN addgroup --system lion && adduser --system --ingroup lion lion
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" asyncpg "python-jose[cryptography]" "pydantic[email]" python-multipart aiohttp
COPY . .
RUN chown -R lion:lion /app
USER lion
EXPOSE 8011
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]
