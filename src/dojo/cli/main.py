"""Dojo.ml CLI — main entry point."""

import typer

from dojo._version import __version__

app = typer.Typer(
    name="dojo",
    help="Dojo.ml — AI-powered experiment orchestration",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"Dojo.ml v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Dojo.ml CLI."""


@app.command()
def start(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to listen on"),
    no_frontend: bool = typer.Option(
        False, "--no-frontend", help="Skip launching the frontend dev server"
    ),
) -> None:
    """Start the Dojo.ml server."""
    from dojo.cli.start import start as _start

    _start(host=host, port=port, no_frontend=no_frontend)


@app.command()
def run(
    prompt: str = typer.Argument(help="The task prompt to run"),
    host: str = typer.Option("127.0.0.1", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
) -> None:
    """Submit a task to a running Dojo.ml server."""
    from dojo.cli.run import run as _run

    _run(prompt=prompt, host=host, port=port)


# Register config subcommand group
from dojo.cli.config import config_app  # noqa: E402

app.add_typer(config_app, name="config")

# Register domain subcommand group
from dojo.cli.domain import app as domain_app  # noqa: E402

app.add_typer(domain_app, name="domain")
