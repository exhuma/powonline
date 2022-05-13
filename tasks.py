import os

from fabric import task

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
def run(ctx):
    ctx.run("./env/bin/python autoapp.py", pty=True)
