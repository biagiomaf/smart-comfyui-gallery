FROM python:3.12-slim

# Install system packages
ENV DEBIAN_FRONTEND=noninteractive

# Make use of apt-cacher-ng if available
RUN if [ "A${BUILD_APT_PROXY:-}" != "A" ]; then \
        echo "Using APT proxy: ${BUILD_APT_PROXY}"; \
        printf 'Acquire::http::Proxy "%s";\n' "$BUILD_APT_PROXY" > /etc/apt/apt.conf.d/01proxy; \
    fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates wget gnupg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN apt-get update -y --fix-missing --no-install-recommends \
    && apt-get install -y --no-install-recommends \
    apt-utils \
    locales \
    ca-certificates \
    sudo \
    curl \
    libgl1 \
    libglib2.0-0 \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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
RUN chown -R smartgallerytoo:smartgallerytoo /app

USER smartgallerytoo

# Install uv
# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/smartgallerytoo/.local/bin/:$PATH"
ENV UV_PROJECT_ENVIRONMENT=venv

# Verify that python3 and uv are installed
RUN which python3 && python3 --version
RUN which uv && uv --version

COPY requirements.txt /app/requirements.txt
RUN --mount=type=cache,target=/uv_cache,uid=1025,gid=1025,mode=0755 \
    export UV_CACHE_DIR=/uv_cache \
    && cd /app \
    && uv venv venv \
    && VIRTUAL_ENV=/app/venv uv pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org \
    && test -d /app/venv \
    && test -f /app/venv/bin/activate \
    && test -x /app/venv/bin/python3 \
    && VIRTUAL_ENV=/app/venv uv pip install uv \
    && test -x /app/venv/bin/uv \
    && unset UV_CACHE_DIR

ARG CHOOSEN_TEMPLATE_FILE
ARG CHOOSEN_SMARTGALLERY_FILE
COPY ${CHOOSEN_SMARTGALLERY_FILE} /app/smartgallery.py
COPY ${CHOOSEN_TEMPLATE_FILE} /app/templates/

USER root

COPY --chmod=555 docker_init.bash /smartgallery_init.bash

EXPOSE 8189

# Remove APT proxy configuration and clean up APT downloaded files
RUN rm -rf /var/lib/apt/lists/* /etc/apt/apt.conf.d/01proxy \
    && apt-get clean

USER smartgallerytoo

CMD ["/smartgallery_init.bash"]

LABEL org.opencontainers.image.source=https://github.com/biagiomaf/smart-comfyui-gallery
