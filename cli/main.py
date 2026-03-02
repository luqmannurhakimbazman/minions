"""Typer CLI for the Minions orchestrator."""

import typer
import httpx
from rich.console import Console
from rich.table import Table

from common.config import get_settings

app = typer.Typer(name="minion", help="Minions task orchestrator CLI.")
console = Console()


def _base_url() -> str:
    return get_settings().api_base_url


@app.command()
def run(description: str = typer.Argument(..., help="Task description"),
        repo: str = typer.Argument(..., help="Repository (owner/name)")):
    """Submit a new task."""
    resp = httpx.post(f"{_base_url()}/tasks", json={"description": description, "repo": repo})
    resp.raise_for_status()
    data = resp.json()
    console.print(f"Task created: [bold]{data['id']}[/bold]  Status: {data['status']}")


@app.command()
def status():
    """List all tasks."""
    resp = httpx.get(f"{_base_url()}/tasks")
    resp.raise_for_status()
    tasks = resp.json()

    table = Table(title="Tasks")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Repo")
    table.add_column("Description")

    for t in tasks:
        table.add_row(
            str(t["id"]),
            t["status"],
            t["repo"],
            t["description"],
        )

    console.print(table)


@app.command()
def logs(task_id: str = typer.Argument(..., help="Task UUID")):
    """Show logs for a task."""
    resp = httpx.get(f"{_base_url()}/tasks/{task_id}")
    resp.raise_for_status()
    data = resp.json()
    task_logs = data.get("logs", [])
    if not task_logs:
        console.print("[dim]No logs yet.[/dim]")
        return
    for line in task_logs:
        console.print(line)


@app.command()
def cancel(task_id: str = typer.Argument(..., help="Task UUID")):
    """Cancel a running task."""
    resp = httpx.post(f"{_base_url()}/tasks/{task_id}/cancel")
    resp.raise_for_status()
    data = resp.json()
    console.print(f"Task {data['id']} is now [bold]{data['status']}[/bold]")


if __name__ == "__main__":
    app()
