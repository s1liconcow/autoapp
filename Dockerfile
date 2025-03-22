ARG PYTHON_VERSION=3.10-slim-bookworm

FROM python:${PYTHON_VERSION} 

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
ENV SQLITE_DB_PATH /data/

RUN apt-get update && apt-get install -y \
lsb-release \
gnupg \
curl \
sqlite3 \
build-essential \
git \
procps \
htop \
apt-get update && \
apt-get install -y caddy && \
apt-get clean

RUN mkdir -p $APP_HOME

WORKDIR $APP_HOME

COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/

COPY . .

CMD ["fastapi", "dev", "--host=0.0.0.0"]
EXPOSE 8000