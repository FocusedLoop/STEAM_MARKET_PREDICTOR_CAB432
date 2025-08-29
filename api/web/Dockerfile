FROM python:3.11-slim

WORKDIR /web

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "web_page.py", "--server.port=3009", "--server.address=0.0.0.0"]