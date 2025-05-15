from fabric import task


@task
def develop(context):
    """
    Set up a development environment
    """
    context.run("uv sync --group test", replace_env=False, pty=True)
    context.run("mkdir -p .mamerwiselen/powonline")
    context.run("cp app.ini.dist .mamerwiselen/powonline/app.ini")
    context.run("pre-commit install -f")


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
            "uv run uvicorn "
            "--reload "
            "--log-level debug "
            "--log-config .devcontainer/logging.yaml "
            "--factory powonline.main:create_app"
        ),
        replace_env=False,
        pty=True,
    )
