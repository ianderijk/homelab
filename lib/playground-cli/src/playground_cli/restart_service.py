from playground_cli.utils import ROOT, SERVICE_MAPPING, logger, run_command


def restart_service(service: str, build: bool = False) -> None:
    parent_dir = next(x for x, y in SERVICE_MAPPING.items() if service in y)
    compose_path = ROOT / parent_dir / service / "docker-compose.yml"
    env_file = ROOT / parent_dir / service / ".env"

    logger.debug(f"Removing container: {service}")
    run_command(f"docker compose -f {compose_path} down --remove-orphans")

    logger.debug(f"Launching container: {service}")
    if env_file.exists():
        command = f"docker compose --env-file {env_file} -f {compose_path} up -d"
    else:
        command = f"docker compose -f {compose_path} up -d"

    if build:
        command += " --build"

    run_command(command)
    logger.info(f"{service} restarted")
