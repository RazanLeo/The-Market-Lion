FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn redis aiokafka aiohttp numpy pandas
COPY . .
CMD ["python", "-m", "uvicorn", "whale_tracker:app", "--host", "0.0.0.0", "--port", "8012"]

