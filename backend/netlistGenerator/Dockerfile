FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    OPENCODE_API_KEY=${OPENCODE_API_KEY} \
    OPENCODE_API_BASE=${OPENCODE_API_BASE} \
    OPENCODE_MODEL=${OPENCODE_MODEL}

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]