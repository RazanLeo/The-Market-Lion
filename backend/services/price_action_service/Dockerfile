FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn redis numpy pandas
COPY . .
CMD ["python", "-m", "uvicorn", "price_action:app", "--host", "0.0.0.0", "--port", "8010"]

