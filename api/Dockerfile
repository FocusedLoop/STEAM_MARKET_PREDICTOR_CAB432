FROM python:3.11-slim

RUN apt-get update \
    && apt-get -yy install libmariadb3 libmariadb-dev gcc

# S3 setup
COPY ../shared /shared/
COPY ../setup.py /shared/
RUN pip install -e /shared

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host=0.0.0.0", "--port=3010"]