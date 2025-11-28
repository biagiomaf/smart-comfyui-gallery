FROM python:3.12-slim

# Install system packages
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y --fix-missing\
    && apt-get install -y \
    apt-utils \
    locales \
    ca-certificates \
    sudo \
    && apt-get upgrade -y \
    && apt-get clean

# UTF-8
RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG=en_US.utf8
ENV LC_ALL=C

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

COPY --chmod=555 docker_init.bash /smartgallery_init.bash

# Every sudo group user does not need a password
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Create a new group for the smartgallery and smartgallerytoo users
RUN groupadd -g 1024 smartgallery \ 
    && groupadd -g 1025 smartgallerytoo

# The smartgallery (resp. smartgallerytoo) user will have UID 1024 (resp. 1025), 
# be part of the smartgallery (resp. smartgallerytoo) and users groups and be sudo capable (passwordless) 
RUN useradd -u 1024 -d /home/smartgallery -g smartgallery -s /bin/bash -m smartgallery \
    && usermod -G users smartgallery \
    && adduser smartgallery sudo
RUN useradd -u 1025 -d /home/smartgallerytoo -g smartgallerytoo -s /bin/bash -m smartgallerytoo \
    && usermod -G users smartgallerytoo \
    && adduser smartgallerytoo sudo

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY smartgallery.py /app/smartgallery.py
COPY templates/* /app/templates/
COPY static /app/static

EXPOSE 8189

USER smartgallerytoo

CMD ["/smartgallery_init.bash"]

LABEL org.opencontainers.image.source=https://github.com/biagiomaf/smart-comfyui-gallery
