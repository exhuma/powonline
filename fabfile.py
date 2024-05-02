import os

from fabric import task


@task
def develop(context):
    """
    Set up a development environment
    """
    context.run(
        "[ -d env ] || python3 -m venv env", replace_env=False, pty=True
    )
    context.run("./env/bin/pip install -U pip", replace_env=False, pty=True)
    context.run(
        "./env/bin/pip install -e .[dev,test]", replace_env=False, pty=True
    )
    context.run("mkdir -p .mamerwiselen/powonline", replace_env=False, pty=True)
    context.run(
        "cp app.ini.dist .mamerwiselen/powonline/app.ini",
        replace_env=False,
        pty=True,
    )
    context.run("pre-commit install -f", replace_env=False, pty=True)


@task
def build_docker(ctx, datever, environment="staging"):  # type: ignore
    tag = f"registry.digitalocean.com/michel-albert/powonline-api:{datever}"
    ctx.run(f"docker build -t {tag} .", replace_env=False, pty=True)


@task
def push(ctx, datever, environment="staging"):  # type: ignore
    tag = f"registry.digitalocean.com/michel-albert/powonline-api:{datever}"
    ctx.run(f"docker push {tag}", pty=True, replace_env=False)


@task
def run(context):
    """
    Run a development server
    """
    context.run(
        (
            "./env/bin/uvicorn "
            "--reload "
            "--log-level debug "
            "--log-config .devcontainer/logging.yaml "
            "--factory powonline.main:create_app"
        ),
        replace_env=False,
        pty=True,
    )
