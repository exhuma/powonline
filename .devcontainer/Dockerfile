FROM mcr.microsoft.com/vscode/devcontainers/python:3.12-bullseye
ENV PYTHONUNBUFFERED 1
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    postgresql-client \
    vim-nox
