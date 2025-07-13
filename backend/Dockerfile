FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gnupg2 \
    wget \
    libgomp1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/faiss_store && chmod -R 777 /app/faiss_store

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]