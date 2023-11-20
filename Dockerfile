FROM --platform=linux/amd64 python:3.10-slim

RUN apt-get -y update

RUN apt-get -y upgrade

RUN apt-get install -y gnupg2 wget curl

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -

RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

RUN apt-get -y update

RUN apt-get install -y google-chrome-stable

RUN apt-get install -yqq unzip

ENV DISPLAY=:99

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY run.py run.py

COPY . app

CMD ["python3", "run.py"]