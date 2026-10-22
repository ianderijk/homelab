import logging
import os
import subprocess
from pathlib import Path
from typing import Any, NamedTuple

ROOT = Path(__file__).parents[4] / "infra"

logger = logging.getLogger("playground")
logger.setLevel("DEBUG")
file_handler = logging.FileHandler(ROOT / "playground.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

SERVICE_MAPPING = {
    "core": ("postgres", "pypi"),
    "storage": ("rustfs",),
    # "services": ("log-listener"),
    "apis": ("chapflix_api",),
    "apps": ("chapflix",),
}
SERVICE_GROUPS = SERVICE_MAPPING.keys()


class Service(NamedTuple):
    compose: Path
    env: Path | None


def run_command(command: str, check: bool = True, logger=logger) -> Any:
    logger.debug(f"Running command '{command}'...")
    command = "mise exec -- " + command
    try:
        result = subprocess.run(
            command, shell=True, check=check, text=True, capture_output=True
        )
        logger.info("Command run successfully")
        return result
    except subprocess.CalledProcessError as e:
        logger.critical(f"Failed to run command, exception: {e}")
        raise


def create_services() -> dict[str, list]:
    logger.info("Finding compose files")
    services = {k: [] for k in SERVICE_GROUPS}
    for service in SERVICE_GROUPS:
        service_path = ROOT / service
        for root, _, files in os.walk(service_path):
            if any("docker-compose" in x for x in files):
                service_group = Path(root).parent.stem
                compose_path = Path(root) / "docker-compose.yml"
                env_path = Path(root) / ".env"
                env_file = env_path if env_path.exists() else None
                service_obj = Service(compose_path, env_file)
                services[service_group].append(service_obj)
                logger.debug(f"Found {compose_path}")
    return services
