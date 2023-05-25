.. >>> Shields >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

.. image:: https://travis-ci.org/exhuma/powonline.svg?branch=develop
    :target: https://travis-ci.org/exhuma/powonline

.. <<< Shields <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

Pow
===

This repository contains an application to help out with a local event.

Required Environment Variables
==============================

POWONLINE_DSN
    The database DSN (f.ex.: ``postgresl://user:password@host/dbname``)


Development Setup (Recommended)
===============================

To ensure reproducible development environments, the project uses
"dev-containers" since March 2023.

Dev-Containers can be used standalone, or, via the VS-Code "Remote Development"
extension. The latter is well integrated and allows for seamless project setup.

All the required files are located in the ``.devcontainer`` folder in the
project root. This is picked up by VS-Code and you can simply select the
"Reopen in Container" option from the command pallette (normally also provided
via a small popup when the project is loaded).

Database Migrations
-------------------

The dev-container initialises everything automatically and no additional step
is needed.

During development, all ``alembic`` tasks can simply be executed from whithin
the ``database`` subfolder.

The production application container contains a separate entry-point
``/upgrade-db.bash`` to trigger the migrations. Simply execute it as follows
whenever needed::

    docker run \
        --rm \
        -e POWONLINE_DSN=<dsn> \
        --entrypoint /upgrade-db.bash \
        <image-id>

On k8s style deployments, this can be executed in init-containters for example.


Development Setup (legacy)
==========================

You need:

* `git <https://git-scm.com>`_
* `Python 3 <https://www.python.org>`_ (On debian & derivatives you also need
  the package ``python3-venv``).
* `fabric <http://www.fabfile.org/>`_
* `pip <https://pip.pypa.io/en/stable/>`_ (should be automatically available in
  Python 3 Virtual Environments).

Bootstrapping a development environment:

Once you have at least git and Python (including ``python-venv`` on debian)
installed, run the following commands::

    git clone https://github.com/exhuma/powonline
    cd powonline
    git checkout develop
    fab develop

After the above steps are run you should be able to run the backend using the
following command::

    $ fab run


Setup for Questionnaires
========================

As of this writing (for version 2019.04.0), the questionnaires are not yet
managed via the web app and two steps need to be done to make questionnaire
scores work:

* Manually add the questionnaire to the database
* Edit the config file and map the questionnaire name to the station name where
  it should be used (multiple entries can exist)::

    [questionnaire-map]
    ; Maps questionnaires to stations. When opening a station dashboard, the
    ; edit-box for questionnaire scores will be linked to the mapped
    ; questionnaire on that station
    questionnaire_name = station_name


Authentication
==============

The frontent authenticates using an OAuth provider like Google or Facebook. If
a user does not exist yet it will be automatically created in the DB with
default (no) permissions. In order to make the application usable at least one
user needs the "admin" role.

This can be done on the CLI with the following command::

    flask grant-admin <username>

The permission can be revoked again using::

    flask revoke-admin <username>

Existing users can be listed with::

    flask list-users
