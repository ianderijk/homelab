import typer
import os
from playground_cli.restore import restore_services
from playground_cli.restart_service import restart_service
from playground_cli.stop_service import stop_single_service, stop_all_services

SERVICES = [
    "chapflix_api",
    "chaps_chores_api",
    "chapflix",
    "chaps_chores",
    "postgres",
    "pypi",
    "vault",
    "kaneo",
]

app = typer.Typer(help="Playground management CLI")


@app.command()
def restore():
    restore_services()


@app.command()
def restart(service: str):
    if service not in SERVICES:
        typer.echo(f"{service} not found")
        os._exit(1)
    typer.echo(f"Restarting {service}...")
    restart_service(service)
    typer.echo(f"{service} restarted")


@app.command()
def stop(service: str):
    if service not in SERVICES:
        typer.echo(f"{service} not found.")
        os._exit(1)
    typer.echo(f"Stopping {service}...")
    stop_single_service(service)
    typer.echo(f"{service} stopped")


@app.command()
def stop_all():
    typer.echo("Stopping all services...")
    stop_all_services()
    typer.echo("All services stopped")


if __name__ == "__main__":
    app()
