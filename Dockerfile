ARG PYTHON_VERSION=3.10-slim-bookworm

FROM python:${PYTHON_VERSION} 

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
ENV SQLITE_DB_PATH /data/
RUN mkdir -p $APP_HOME

WORKDIR $APP_HOME

COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/

COPY . .

CMD ['fastapi', 'run']
EXPOSE 8000