import os

import typer

from package_setup.constants import LIB_ROOT
from package_setup.setup_dirs import create_project_directories
from package_setup.setup_uv import setup_uv

app = typer.Typer(help="Python project setup")


@app.command()
def package(name: str):
    project_path = LIB_ROOT / name
    if not project_path.exists():
        os.mkdir(project_path)
    os.chdir(project_path)
    create_project_directories(name)
    setup_uv(name)


if __name__ == "__main__":
    app()
