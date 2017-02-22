Deployment
------------

The Docker configuration settings allows you to deploy it fast. With ``docker`` running
and ``docker-compose`` installed, copy the ``env.example`` to ``.env``, configure it with
your settings and execute the following commands:

.. code-block:: bash
    docker-compose build
    docker-compose up

You can access your ``osmcha-django`` instance in http://localhost/ at your browser.

It is also possible to deploy to Heroku or to your own server by using Dokku, an open
source Heroku clone.

To put celery in production we need a celeryd and a celery beat services running on
the machine. More information: https://celery.readthedocs.org/en/latest/tutorials/daemonizing.html#daemonizing

And we also need to set periodic tasks to import the changesets daily or hourly: https://celery.readthedocs.org/en/latest/userguide/periodic-tasks.html

If you find any issue, please report. We didn't test it in Heroku and Dokku

Heroku
^^^^^^

Run these commands to deploy the project to Heroku:

.. code-block:: bash

    heroku create --buildpack https://github.com/heroku/heroku-buildpack-python

    heroku addons:create heroku-postgresql:hobby-dev
    heroku pg:backups schedule --at '02:00 America/Los_Angeles' DATABASE_URL
    heroku pg:promote DATABASE_URL

    heroku addons:create heroku-redis:hobby-dev

    heroku config:set DJANGO_SECRET_KEY=`openssl rand -base64 32`
    heroku config:set DJANGO_SETTINGS_MODULE='config.settings.production'
    heroku config:set POSTGRES_USER='postgresuser'
    heroku config:set POSTGRES_PASSWORD='mysecretpass'
    heroku config:set OAUTH_OSM_KEY='your_osm_oauth_key'
    heroku config:set OAUTH_OSM_SECRET='your_osm_oauth_secret'

    heroku config:set PYTHONHASHSEED=random

    git push heroku master
    heroku run python manage.py migrate
    heroku run python manage.py check --deploy
    heroku run python manage.py createsuperuser
    heroku open

Dokku
^^^^^

You need to make sure you have a server running Dokku with at least 1GB of RAM. Backing services are
added just like in Heroku however you must ensure you have the relevant Dokku plugins installed.

.. code-block:: bash

    cd /var/lib/dokku/plugins
    git clone https://github.com/rlaneve/dokku-link.git link
    git clone https://github.com/dokku/dokku-rabbitmq redis
    git clone https://github.com/jezdez/dokku-postgres-plugin postgres
    dokku plugins-install

You can specify the buildpack you wish to use by creating a file name .env containing the following.

.. code-block:: bash

    export BUILDPACK_URL=<repository>

You can then deploy by running the following commands.

.. code-block:: bash

    git remote add dokku dokku@yourservername.com:osmcha-django
    git push dokku master
    ssh -t dokku@yourservername.com dokku redis:create osmcha-django-redis
    ssh -t dokku@yourservername.com dokku redis:link osmcha-django-redis osmcha-django
    ssh -t dokku@yourservername.com dokku postgres:create osmcha-django-postgres
    ssh -t dokku@yourservername.com dokku postgres:link osmcha-django-postgres osmcha-django
    ssh -t dokku@yourservername.com dokku config:set osmcha-django DJANGO_SECRET_KEY=RANDOM_SECRET_KEY_HERE
    ssh -t dokku@yourservername.com dokku config:set osmcha-django DJANGO_SETTINGS_MODULE='config.settings.production'
    ssh -t dokku@yourservername.com dokku config:set osmcha-django POSTGRES_USER='postgresuser'
    ssh -t dokku@yourservername.com dokku config:set osmcha-django POSTGRES_PASSWORD='mysecretpass'
    ssh -t dokku@yourservername.com dokku config:set osmcha-django OAUTH_OSM_KEY='your_osm_oauth_key'
    ssh -t dokku@yourservername.com dokku config:set osmcha-django OAUTH_OSM_SECRET='your_osm_oauth_secret'
    ssh -t dokku@yourservername.com dokku run osmcha-django python manage.py migrate
    ssh -t dokku@yourservername.com dokku run osmcha-django python manage.py createsuperuser

When deploying via Dokku make sure you backup your database in some fashion as it is NOT done automatically.
