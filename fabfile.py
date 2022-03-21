from fabric import task


@task
def develop(context):
    """
    Set up a development environment
    """
    context.run("[ -f env ] || python3 -m venv env", replace_env=False)
    context.run("./env/bin/pip install -U pip", replace_env=False)
    context.run("./env/bin/pip install -e .[dev,test]", replace_env=False)
