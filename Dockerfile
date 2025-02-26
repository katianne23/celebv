FROM python:3.10

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install yt-dlp opencv-python-headless

CMD ["python", "download_and_process.py"]
FROM python:3.10

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install yt-dlp opencv-python-headless

CMD ["python", "download_and_process.py"]
