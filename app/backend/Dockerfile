FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc libpq-dev curl ca-certificates \
      libta-lib0-dev wget \
    && rm -rf /var/lib/apt/lists/*

# TA-Lib C library (pandas-ta works without it; TA-Lib python wrapper needs it)
RUN cd /tmp && wget -q https://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar xzf ta-lib-0.4.0-src.tar.gz && cd ta-lib && ./configure --prefix=/usr && make && make install \
    && cd / && rm -rf /tmp/ta-lib*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
