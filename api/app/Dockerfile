FROM python:3.11-slim

RUN apt-get update \
    && apt-get -yy install libmariadb3 libmariadb-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# S3 setup
COPY shared /shared/
WORKDIR /shared
RUN pip install -e .

WORKDIR /app

COPY app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

CMD ["python3", "-m", "uvicorn", "main:app", "--host=0.0.0.0", "--port=3010"]