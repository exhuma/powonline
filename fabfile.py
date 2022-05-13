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
    context.run("pre-commit install", replace_env=False, pty=True)


@task
def build_python_package(ctx):  # type: ignore
    ctx.run("./env/bin/python setup.py sdist")
    fullname = ctx.run("./env/bin/python setup.py --fullname")
    tar_name = "dist/%s.tar.gz" % fullname.stdout.strip()


@task
def build_docker(ctx, datever, environment="staging"):  # type: ignore
    build_python_package(ctx)
    fullname = ctx.run("./env/bin/python setup.py --fullname")
    tar_name = "%s.tar.gz" % fullname.stdout.strip()
    tag = f"registry.albert.lu/exhuma/powonline-api:{datever}"
    ctx.run(
        f"docker build -t {tag} --build-arg PKGFILE={tar_name} .",
        replace_env=False,
        pty=True,
    )


@task
def deploy(ctx, datever, environment="staging"):  # type: ignore
    tag = f"registry.albert.lu/exhuma/powonline-api:{datever}"
    ctx.run(f"docker push {tag}", pty=True, replace_env=False)


@task
def run(context):
    """
    Run a development server
    """
    context.run("./env/bin/python autoapp.py", replace_env=False, pty=True)
