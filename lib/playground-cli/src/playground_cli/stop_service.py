from playground_cli.utils import (
    ROOT,
    SERVICE_MAPPING,
    create_services,
    logger,
    run_command,
)


def stop_single_service(service: str) -> None:
    logger.debug(f"Stopping {service}...")
    parent_dir = next(x for x, y in SERVICE_MAPPING.items() if service in y)
    compose_path = ROOT / parent_dir / service / "docker-compose.yml"
    run_command(f"docker compose -f {compose_path} down --remove-orphans")
    logger.info(f"{service} stopped")


def stop_all_services() -> None:
    logger.debug("Stopping all service...")
    services_map = create_services()
    services = [
        service for service_list in services_map.values() for service in service_list
    ]
    for service in services:
        logger.debug(f"Stopping {service.compose}")
        run_command(f"docker compose -f {service.compose} down --remove-orphans")
    logger.info("All services stopped")
