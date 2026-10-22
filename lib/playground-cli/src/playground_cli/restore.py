from playground_cli.utils import SERVICE_GROUPS, create_services, logger, run_command

logger.debug("Starting lakehouse accelerator restoration")

NETWORK_NAME = "lakehouse-net"


def create_docker_network() -> None:
    logger.debug("Removing docker network")
    run_command(f"docker network rm {NETWORK_NAME}", check=False)
    logger.debug("Creating docker network")
    run_command(f"docker network create {NETWORK_NAME}", check=False)


SERVICES = create_services()


def remove_partial_containers() -> None:
    logger.debug("Removing any partially running containers")
    # reverse ordering here to remove core services last
    for group in reversed(SERVICE_GROUPS):
        services = SERVICES.get(group, [])
        for service in services:
            run_command(f"docker compose -f {service.compose} down --remove-orphans")


def launch_containers(build: bool) -> None:
    logger.debug("Launching containers")
    for group in SERVICE_GROUPS:
        compose_files = SERVICES.get(group, [])
        for service in compose_files:
            service_name = service.compose.parent.stem
            logger.debug(f"Launching {service_name}")
            has_env = service.env is not None

            if has_env:
                command = f"docker compose --env-file {service.env} -f {service.compose} up -d"
            else:
                command = f"docker compose -f {service.compose} up -d"
            if build:
                command += " --build"

            run_command(command)
    logger.info("Containers launched successfully")


def restore_services(build: bool = False) -> None:
    logger.debug("Starting lakehouse accelerator restoration script")
    print("==========================================================")
    print("          PLAYGROUND MONOREPO RESTORATION START           ")
    print("==========================================================")
    print("Purging partial containers...")
    remove_partial_containers()
    print("Creating docker network...")
    create_docker_network()
    print("Launching containers...")
    launch_containers(build)
    print("==========================================================")
    print("           PLAYGROUND MONOREPO RESTORATION STOP           ")
    print("==========================================================")
    logger.info("Lakehouse restored")
