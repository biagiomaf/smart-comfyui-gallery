FROM python:3.12-slim

# Install ffprobe
RUN apt-get update && apt-get install -y ffmpeg \
  && test -x /usr/bin/ffprobe
ENV FFPROBE_MANUAL_PATH=/usr/bin/ffprobe

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PYTHONIOENCODING=utf-8

RUN mkdir -p /app/templates

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY smartgallery.py /app/smartgallery.py
COPY templates/* /app/templates/

EXPOSE 8189

CMD ["python", "smartgallery.py"]
