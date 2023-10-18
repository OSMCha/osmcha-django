FROM python:3.10-slim-bookworm
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq -y \
    && apt-get install -y curl wget python3 python3-dev python3-pip git \
    libgeos-dev libcurl4-gnutls-dev librtmp-dev python3-gdal libyaml-dev \
    locales nginx supervisor postgresql-client libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Requirements have to be pulled and installed here, otherwise caching won't work
COPY ./requirements /requirements

RUN pip install -r /requirements/production.txt

COPY . /app
RUN useradd django
RUN chown -R django:django /app

COPY ./compose/django/gunicorn.sh /gunicorn.sh
COPY ./compose/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r//' /entrypoint.sh \
    && sed -i 's/\r//' /gunicorn.sh \
    && chmod +x /entrypoint.sh \
    && chmod +x /gunicorn.sh

WORKDIR /app
USER django

ENTRYPOINT ["/entrypoint.sh"]
