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
    The database DSN (f.ex.: ``postgresql://user:password@host/dbname``)


Development Setup (Recommended)
===============================

To ensure reproducible development environments, the project uses
"dev-containers" since March 2023.

Dev-Containers can be used standalone, or, via the VS-Code "Remote Development"
extension. The latter is well integrated and allows for seamless project setup.

All the required files are located in the ``.devcontainer`` folder in the
project root. This is picked up by VS-Code and you can simply select the
"Reopen in Container" option from the command palette (normally also provided
via a small popup when the project is loaded).

Authentication Setup
--------------------

1. Obtain OAuth2 credentials for Google and Facebook:
   - For Google, create credentials in the Google Cloud Console and note the
     client ID, client secret, and redirect URI.
   - For Facebook, create an app in the Facebook Developer Console and note the
     client ID, client secret, and redirect URI.

2. Add the credentials to your environment variables or configuration file
   (e.g., ``app.ini``).

3. Ensure the redirect URIs match the ones configured in the respective
   developer consoles.

Database Migrations
-------------------

The dev-container initializes everything automatically, and no additional step
is needed.

During development, all ``alembic`` tasks can simply be executed from within
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

Running the Application
-----------------------

1. Start the development container in VS Code.
2. Ensure all required environment variables are set.
3. Run the application using the provided scripts (e.g., ``run-api.sh``).
4. Access the application in your browser at the specified URL.


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


Authentication
==============

Local Development Users
-----------------------

For local development, the application supports HTTP Basic Authentication via
the `local_dev_user` function. This method is intended **only** for development
purposes and provides **zero security**. It should never be used in production.

To use this feature:

1. When prompted for a username, use the format:
   ```
   username#role1,role2,...
   ```
   - Replace `username` with the desired username.
   - Replace `role1,role2,...` with a comma-separated list of roles. Valid roles include:
     - `admin`
     - `staff`
     - `station_manager`

2. Any invalid roles will be ignored.

3. Example:
   - Username: `devuser#admin,staff`
   - Password: Any value (not validated).

This will create a development user with the specified roles, allowing you to
test role-based access control in the application.
