import logging

import click

from src.app import app
from src.settings import settings

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)


@click.group(invoke_without_command=True)
@click.option("--port", default=9099)
@click.pass_context
def cli(ctx, port=None):
    if ctx.invoked_subcommand is None:
        # run as normal server
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=port)


@click.command()
@click.option("--port", default=9099)
def live_reload(port=None):
    """Start server with reloading"""

    # run with reload
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)


cli.add_command(live_reload, name="livereload")


if __name__ == "__main__":
    cli()
