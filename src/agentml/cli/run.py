"""CLI run command — submit a task and display results."""

import typer
from rich.console import Console

console = Console()


def run(
    prompt: str = typer.Argument(help="The task prompt to run"),
    host: str = typer.Option("127.0.0.1", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
) -> None:
    """Submit a task to the AgentML server and display the result."""
    import httpx

    base_url = f"http://{host}:{port}"

    console.print(f"\n  [bold]Submitting task:[/bold] {prompt}\n")

    try:
        with httpx.Client(base_url=base_url, timeout=60.0) as client:
            resp = client.post("/tasks", json={"prompt": prompt})
            resp.raise_for_status()
            data = resp.json()

            console.print(f"  [green]✓[/green] Task ID: {data['id']}")
            console.print(f"  [green]✓[/green] Status:  {data['status']}")

            if data.get("summary"):
                console.print(f"  [green]✓[/green] Summary: {data['summary']}")

            if data.get("metrics"):
                console.print("  [bold]Metrics:[/bold]")
                for key, val in data["metrics"].items():
                    console.print(f"    {key}: {val}")

            if data.get("experiments"):
                console.print(f"  [bold]Experiments:[/bold] {len(data['experiments'])}")
                for exp in data["experiments"]:
                    console.print(f"    - {exp['id']} [{exp['state']}]")

            console.print()

    except httpx.ConnectError:
        console.print(
            f"  [red]✗[/red] Could not connect to server at {base_url}\n"
            "    Run [bold]agentml start[/bold] first."
        )
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError as e:
        console.print(f"  [red]✗[/red] Server error: {e.response.status_code}")
        raise typer.Exit(code=1)
