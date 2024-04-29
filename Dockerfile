FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
  wget \
  unzip \
  curl \
  gnupg \
  && rm -rf /var/lib/apt/lists/*

# Install Firefox
RUN apt-get update && apt-get install -y firefox-esr

# Install GeckoDriver
RUN wget -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz
RUN tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/
RUN pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENV DISPLAY=:99

CMD ["python3", "run.py"]