import atexit
import logging
from logging.handlers import DEFAULT_TCP_LOGGING_PORT, SocketHandler
from typing import Literal


class ProjectLogger:
    HOST_IP = "127.0.0.1"

    def __init__(
        self,
        name: str,
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG",
    ) -> None:
        self.logger = logging.getLogger(name)
        self.level = self._set_log_level(level)
        self.socket_handler = None

        self.logger.setLevel(self.level)
        self._set_logger_format()
        self._attach_listener()

        self._program_start()

        atexit.register(self._cleanup)

    def _set_log_level(
        self, level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    ):
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return levels.get(level, logging.INFO)

    def _set_logger_format(self) -> None:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _attach_listener(self) -> None:
        self.socket_handler = SocketHandler(
            ProjectLogger.HOST_IP, DEFAULT_TCP_LOGGING_PORT
        )
        self.logger.addHandler(self.socket_handler)

    def _cleanup(self) -> None:
        self._program_end()
        if self.socket_handler:
            self.socket_handler.close()
            self.logger.removeHandler(self.socket_handler)

    def _program_start(self) -> None:
        self.info("Program starting")

    def _program_end(self) -> None:
        self.info("Program ending")

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def debug(self, msg: str) -> None:
        self.logger.debug(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)

    def critical(self, msg: str) -> None:
        self.logger.critical(msg)
