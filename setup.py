from setuptools import setup, find_packages
VERSION = open('powonline/version.txt').read()
setup(
    name="powonline",
    version=VERSION.strip(),
    packages=find_packages(),
    install_requires=[
        'config-resolver >= 4.2, <5.0',
        'flask',
        'flask-restful',
        'flask-sqlalchemy',
        'gouge >= 1.1, <2.0',
        'psycopg2',
        'sqlalchemy',
    ],
    extras_require={
        'dev': [
            'alembic',
        ],
        'test': [
            'pytest',
            'pytest-cache',
            'pytest-catchlog',
        ]
    },
    include_package_data=True,
    author="Michel Albert",
    author_email="michel@albert.lu",
    description="Tracker for PowWow 2017",
    license="BSD",
    url="http://exhuma.github.com/powonline",
)
