"""CLI start command — launches the uvicorn server."""

import typer
from rich.console import Console

from agentml._version import __version__

console = Console()


def start(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to listen on"),
) -> None:
    """Start the AgentML server."""
    import uvicorn

    from agentml.api.app import create_app
    from agentml.config.settings import Settings

    settings = Settings.load()
    settings.api.host = host
    settings.api.port = port

    # Print startup banner
    console.print()
    console.print(f"  [bold cyan]AgentML[/bold cyan] v{__version__}")
    console.print(f"  ✓ FastAPI server → http://{host}:{port}")
    console.print(f"  ✓ API docs       → http://{host}:{port}/docs")
    console.print()
    console.print("  Press Ctrl+C to stop.")
    console.print()

    app = create_app(settings)
    uvicorn.run(app, host=host, port=port, log_level="info")
