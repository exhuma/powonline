.. >>> Shields >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

.. image:: https://travis-ci.org/exhuma/powonline.svg?branch=develop
    :target: https://travis-ci.org/exhuma/powonline

.. <<< Shields <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

Pow
===

This repository contains an application to help out with a local event. It is
currenlty in a **very early** development stage!


Development Setup
=================

You need:

* `git <https://git-scm.com>`_
* `Python 3 <https://www.python.org>`_ (On debian & derivatives you also need
  the package ``python3-venv``).
* `npm <https://www.npmjs.com>`_
* `fabric <http://www.fabfile.org/>`_
* `pip <https://pip.pypa.io/en/stable/>`_ (should be automatically available in
  Python 3 Virtual Environments).

Bootstrapping a development environment:

Once you have at least git, Python (including ``python-venv`` on debian) and
Docker installed, run the following commands::

    git clone https://github.com/exhuma/powonline
    cd powonline
    git checkout develop
    fab develop   # <-- This step will take a while!

After the above steps are run you should be able to run both the frontend and
backend using the following two commands::

    $ ./env/bin/python autoapp.py     # Backend
    $ (cd frontend/powonline && npm run dev)    # Frontend

.. note::

    **IMPORTANT**

    You will need to set the variable ``BASE_URL`` in
    ``frontend/powonline/src/main.js`` so that the frontend connects to the
    proper backend!


Adding a user to the database
-----------------------------

By default user passwords are stored hashed in the database.

Adding a user (or replacing the user's password) can be done using the
fabric task ``set_password``::

    fab set_password


.. note::

    In order to simplify administrative tasks, the user table contains a flag
    ``password_is_plaintext``. This indicates that a password is stored as
    plain-text. If a user with a plain-text password logs in, it will
    automatically be hashed. This is mainly used to help during development
    without to much hassle, but should not be used during production!
