from setuptools import find_packages, setup

with open("powonline/version.txt") as fptr:
    VERSION = fptr.read()

setup(
    name="powonline",
    version=VERSION.strip(),
    packages=find_packages(),
    install_requires=[
        "bcrypt",
        "config-resolver >= 4.2, <5.0",
        "flask",
        "imapclient",
        "flask-restful",
        "flask-sqlalchemy",
        "gouge >= 1.1, <2.0",
        "marshmallow",
        "pillow",
        "psycopg2-binary",
        "pusher",
        "pyjwt",
        "python-dateutil",
        "requests_oauthlib",
        "sqlalchemy",
    ],
    extras_require={
        "dev": [
            "alembic",
            "blessings",
            "gouge",
        ],
        "test": [
            "flask-testing",
            "pytest",
            "pytest-catchlog",
            "pytest-coverage",
            "pytest-xdist",
        ],
    },
    entry_points={
        "flask.commands": [
            "grant-admin=powonline.cli:grant_admin",
            "revoke-admin=powonline.cli:revoke_admin",
            "list-users=powonline.cli:list_users",
            "add-local-user=powonline.cli:add_local_user",
            "import-csv=powonline.cli:import_csv",
            "fetch-mails=powonline.cli:fetch_mails",
        ]
    },
    include_package_data=True,
    author="Michel Albert",
    author_email="michel@albert.lu",
    description="Tracker for PowWow 2017",
    license="BSD",
    url="https://exhuma.github.com/powonline",
)
