FROM python:3.11-slim

RUN apt-get update \
    && apt-get -yy install libmariadb3 libmariadb-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /api

# S3 setup
COPY api/shared /shared/
WORKDIR /shared
RUN pip install -e .

WORKDIR /api
COPY api/app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY api/app/ ./app

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host=0.0.0.0", "--port=3010", "--workers=4"]