from fabric import task


@task
def develop(context):
    """
    Set up a development environment
    """
    context.run("uv sync", replace_env=False, pty=True)
    context.run("mkdir -p .mamerwiselen/powonline")
    context.run("cp sample-files/app.ini .mamerwiselen/powonline/app.ini")
    context.run("pre-commit install -f")


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
