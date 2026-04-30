FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn aiohttp motor redis aiokafka asyncpg python-jose passlib pydantic numpy pandas aiofiles
COPY . .
CMD ["python", "-m", "uvicorn", "main:app --host 0.0.0.0 --port 8007"]

