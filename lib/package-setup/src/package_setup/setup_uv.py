import os
import subprocess

from package_setup.constants import LIB_ROOT


def setup_uv(name: str) -> None:
    os.chdir(LIB_ROOT / name)
    subprocess.run(["uv", "init"], check=False)
