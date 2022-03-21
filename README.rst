.. >>> Shields >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

.. image:: https://travis-ci.org/exhuma/powonline.svg?branch=develop
    :target: https://travis-ci.org/exhuma/powonline

.. <<< Shields <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

Pow
===

This repository contains an application to help out with a local event.


Development Setup
=================

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

    $ ./env/bin/python autoapp.py


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
