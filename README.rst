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
* `pip <https://pip.pypa.io/en/stable/>`_ (should be automatically available in
  Python 3 Virtual Environments).

Bootstrapping a development environment:

Once you have at least git, Python (including ``python-venv`` on debian) and
Docker installed, run the following commands::

    git clone https://github.com/exhuma/powonline
    cd powonline
    git checkout develop
    python3 -m venv env
    ./env/bin/pip install fabric
    ./env/bin/fab develop   # <-- This step will take a while!

After the above steps are run you should be able to run both the frontend and
backend using the following two commands::

    $ ./env/bin/python autoapp.py     # Backend
    $ (cd frontend && npm run dev)    # Frontend


.. note::

    **IMPORTANT**

    You will need to set the variable ``BASE_URL`` in
    ``frontend/powonline/src/main.js`` so that the frontend connects to the
    proper backend!
