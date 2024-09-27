osmcha-django
==============

.. image:: https://coveralls.io/repos/github/osmcha/osmcha-django/badge.svg?branch=master
    :target: https://coveralls.io/github/willemarcel/osmcha-django?branch=master

.. image:: https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg
    :target: code_of_conduct.md


The aim of OSMCHA is to help identify and fix harmful edits in the OpenStreetMap.
It relies on `OSMCHA <https://github.com/willemarcel/osmcha>`_ to analyse the changesets.

This project provides a Django application that gets changesets from the
OpenStreetMap API, analyses and stores them in a database and finally provides a
REST API to interact with the changeset data.

This repository contains the backend code. You can report errors or request new features in the
`osmcha-frontend repository <https://github.com/osmcha/osmcha-frontend>`_.

License: BSD 2-Clause

OSMCha is an `OpenStreetMap US <https://www.openstreetmap.us/>` charter project. You can support this project by `making a donation <https://openstreetmap.app.neoncrm.com/forms/osmcha>`.

Settings
------------

osmcha-django relies extensively on environment settings which **will not work with
Apache/mod_wsgi setups**. It has been deployed successfully with both Gunicorn/Nginx
and uWSGI/Nginx.

For configuration purposes, the following table maps the 'osmcha-django' environment
variables to their Django settings:


======================================= ================================= ========================================= ===========================================
Environment Variable                    Django Setting                    Development Default                       Production Default
======================================= ================================= ========================================= ===========================================
DJANGO_CACHES                           CACHES (default)                  locmem                                    redis
DJANGO_DEBUG                            DEBUG                             True                                      False
DJANGO_SECRET_KEY                       SECRET_KEY                        CHANGEME!!!                               raises error
DJANGO_SECURE_BROWSER_XSS_FILTER        SECURE_BROWSER_XSS_FILTER         n/a                                       True
DJANGO_SECURE_SSL_REDIRECT              SECURE_SSL_REDIRECT               n/a                                       True
DJANGO_SECURE_CONTENT_TYPE_NOSNIFF      SECURE_CONTENT_TYPE_NOSNIFF       n/a                                       True
DJANGO_SECURE_FRAME_DENY                SECURE_FRAME_DENY                 n/a                                       True
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS   HSTS_INCLUDE_SUBDOMAINS           n/a                                       True
DJANGO_SESSION_COOKIE_HTTPONLY          SESSION_COOKIE_HTTPONLY           n/a                                       True
DJANGO_SESSION_COOKIE_SECURE            SESSION_COOKIE_SECURE             n/a                                       False
DJANGO_DEFAULT_FROM_EMAIL               DEFAULT_FROM_EMAIL                n/a                                       "osmcha-django <noreply@example.com>"
DJANGO_SERVER_EMAIL                     SERVER_EMAIL                      n/a                                       "osmcha-django <noreply@example.com>"
DJANGO_EMAIL_SUBJECT_PREFIX             EMAIL_SUBJECT_PREFIX              n/a                                       "[osmcha-django] "
DJANGO_CHANGESETS_FILTER                CHANGESETS_FILTER                 None                                      None
PGUSER                                  DATABASES                         None                                      None
PGPASSWORD                              DATABASES                         None                                      None
PGHOST                                  DATABASES                         localhost                                 localhost
OAUTH2_OSM_KEY                          SOCIAL_AUTH_OPENSTREETMAP_KEY     None                                      None
OAUTH2_OSM_SECRET                       SOCIAL_AUTH_OPENSTREETMAP_SECRET  None                                      None
DJANGO_ANON_USER_THROTTLE_RATE          ANON_USER_THROTTLE_RATE           None                                      30/min
DJANGO_COMMON_USER_THROTTLE_RATE        COMMON_USER_THROTTLE_RATE         None                                      180/min
DJANGO_NON_STAFF_USER_THROTTLE_RATE     NON_STAFF_USER_THROTTLE_RATE      3/min                                     3/min
OAUTH_REDIRECT_URI                      OAUTH_REDIRECT_URI                http://localhost:8000/oauth-landing.html  http://localhost:8000/oauth-landing.html
DJANGO_ENABLE_CHANGESET_COMMENTS        ENABLE_POST_CHANGESET_COMMENTS    False                                     False
DJANGO_OSM_COMMENTS_API_KEY             OSM_COMMENTS_API_KEY              ''                                        ''
======================================= ================================= ========================================= ===========================================

You can set each of these variables with:

    $ export VAR=VALUE

During the development, you can define the values inside your virtualenv ``bin/activate`` file.


Filtering Changesets
---------------------

You can filter the changesets that will be imported by defining the variable CHANGESETS_FILTER
with the path to a GeoJSON file containing a polygon with the geographical area you want to filter.


Getting up and running
----------------------

Basics
^^^^^^

The steps below will get you up and running with a local development environment.
We assume you have the following installed:

* pip
* virtualenv
* PostgreSQL

Before installing the python libraries, we need to install some packages in the
operational system::

    $ sudo ./install_os_dependencies.sh install

For the next step, make sure to create and activate a virtualenv_, then open a terminal at the project root and install the
requirements for local development::

    $ pip install -r requirements/local.txt

.. _virtualenv: http://docs.python-guide.org/en/latest/dev/virtualenvs/

Create a local PostgreSQL database::

    $ createdb osmcha

Run ``migrate`` on your new database::

    $ python manage.py migrate

You can now run the ``runserver_plus`` command::

    $ python manage.py runserver_plus

Open up your browser to http://127.0.0.1:8000/ to see the site running locally.

Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

To create a **superuser account**, use this command::

    $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

How to login using the OAuth api
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Make a POST request to ``<your_base_url>/api/v1/social-auth/`` to receive the ``oauth_token``, ``oauth_token_secret`` keys.
* Take the ``oauth_token`` and redirect the user to ``https://www.openstreetmap.org/oauth/authorize?oauth_token=<oauth_token>``.
* You'll be redirected to the URL that you configured in your OSM OAuth key settings. That redirect url will contain the ``oauth_verifier`` param.
* Make another POST request to ``<your_base_url>/api/v1/social-auth/`` and send the ``oauth_token``, ``oauth_token_secret`` and ``oauth_verifier`` as the data. You'll receive a token that you can use to make authenticated requests.
* The token key should be included in the Authorization HTTP header. The key should be prefixed by the string literal "Token", with whitespace separating the two strings. For example: ``Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b``.

Frontend
^^^^^^^^

`osmcha-frontend <https://github.com/osmcha/osmcha-frontend>`_ is a web
interface that you can use to interact with the API. The web interface can be
deployed separately and configured to talk to this Django app when making API
requests. See the README in that repository for more details.

Feature creation endpoint
^^^^^^^^^^^^^^^^^^^^^^^^^

The feature creation endpoint allows only admin users to create features. You can
use the admin site to create a token for a user.

Instances
---------

The main instance is https://osmcha.org/. You can check the API
documentation at https://osmcha.org/api-docs/.

There is currently no official staging instance.

Deployment
------------

Check the `Deploy <DEPLOY.rst>`_ file for instructions on how to deploy with Heroku and Dokku.


Get in contact
---------------

If you use, deploy or are interested in helping develop OSMCha, subscribe to our
`mailing list <https://lists.openstreetmap.org/listinfo/osmcha-dev>`_. You can
report errors or request new features in the
`osmcha-frontend repository <https://github.com/osmcha/osmcha-frontend>`_.
