FROM python:3.10-slim-bookworm
ARG DEBIAN_FRONTEND=noninteractive
ARG REQUIREMENTS_FILE=production.txt
ARG DJANGO_SETTINGS_MODULE=config.settings.production

RUN apt-get update -qq -y \
    && apt-get install -y curl wget python3 python3-dev python3-pip git \
    libgeos-dev libcurl4-gnutls-dev librtmp-dev python3-gdal libyaml-dev \
    locales nginx supervisor postgresql-client libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Requirements have to be pulled and installed here, otherwise caching won't work
COPY ./requirements /requirements
RUN pip install -r /requirements/$REQUIREMENTS_FILE

COPY . /app
RUN useradd django
RUN chown -R django:django /app
WORKDIR /app

RUN python manage.py collectstatic --noinput

COPY ./compose/django/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER django
VOLUME /app/staticfiles

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi", "-w", "4", "-b", "0.0.0.0:5000", "--chdir", "/app"]
