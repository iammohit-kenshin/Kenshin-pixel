FROM python:3.11-slim

WORKDIR /app

# Install ffmpeg and other deps
RUN apt-get update && \
    apt-get install -y ffmpeg aria2 && \
    apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
