FROM python:3.10-slim
WORKDIR /web-scrapers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY run.py run.py
COPY . app
CMD ["python3", "run.py"]