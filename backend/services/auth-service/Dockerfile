FROM python:3.11-slim
WORKDIR /app
RUN addgroup --system lion && adduser --system --ingroup lion lion
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" asyncpg "redis[asyncio]" "python-jose[cryptography]" "passlib[argon2]" argon2-cffi pyotp "qrcode[pil]" pillow "pydantic[email]" aiohttp python-multipart slowapi
COPY services/auth-service/ .
RUN chown -R lion:lion /app
USER lion
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
