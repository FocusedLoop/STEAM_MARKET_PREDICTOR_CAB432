FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# S3 setup
COPY api/shared /shared/
WORKDIR /shared
RUN pip install -e .

WORKDIR /api_sklearn

COPY api/sklearn_worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/sklearn_worker/ .

CMD ["python3", "-m", "uvicorn", "api_sklearn:app", "--host=0.0.0.0", "--port=3008"]