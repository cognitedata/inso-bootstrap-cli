import logging.config
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Type

from dependency_injector import containers, providers
from dotenv import load_dotenv

from .app_config import BootstrapCoreConfig, BootstrapDeleteConfig, CommandMode
from .common.cognite_client import CogniteConfig, get_cognite_client


def init_container(
    container_cls: Type[containers.Container],
    config_path: str | Path = "/etc/f25e/config.yaml",
    dotenv_path: str | Path | None = None,
) -> containers.Container:
    """Spinning up container and

    Args:
        container_cls (containers.Container): support different
        config_path (str | Path, optional): _description_. Defaults to "/etc/f25e/config.yaml".
        dotenv_path (str | Path, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    # checks for .env file, loads it and override existing env-variables
    load_dotenv(dotenv_path, override=True)

    container = container_cls()
    container.config.from_yaml(config_path, required=True)  # type: ignore
    container.init_resources()  # i.e.logging

    # logging.debug(f"{container.config()=}")

    return container


def init_logging(logging_config: Optional[dict], deprecated_logger_config: Optional[dict]):
    # https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
    # from logging-cookbook examples for 'logging_config' dict
    # TODO: needed to handle missing log folders?
    if logging_config:
        logging.config.dictConfig(logging_config)

        logging.debug(f"{logging_config=}")

    elif deprecated_logger_config:
        # convert extractorutils logger-config to a standard 'dictConfig'
        # TODO: deprecation warning
        logging.config.dictConfig(
            {
                "version": 1,
                "formatters": {"formatter": {"format": "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"}},
                "handlers": {
                    "file": {
                        "class": "logging.FileHandler",
                        "filename": deprecated_logger_config.get("file", {}).get("path", "./logs/bootstrap.log"),
                        "formatter": "formatter",
                        "mode": "w",
                        "level": deprecated_logger_config.get("file", {}).get("level", "INFO"),
                    },
                    "console": {
                        "class": "logging.StreamHandler",
                        "level": deprecated_logger_config.get("console", {}).get("level", "INFO"),
                        "formatter": "formatter",
                        "stream": "ext://sys.stderr",
                    },
                },
                "root": {"level": "DEBUG", "handlers": ["console", "file"]},
            }
        )
    else:
        # if no logging config given, make a simple one to console only
        logging.basicConfig(
            format="%(asctime)s [%(levelname)-8s] %(threadName)s - %(message)s",
            level=logging.INFO,
            handlers=[
                # logging.FileHandler("./logs/debug.log"),
                logging.StreamHandler()
            ],
        )

    yield logging.getLogger()


def shutdown_container(container):
    logging.debug("function to handle additional shutdown of resources")
    container.shutdown_resources()


class BaseContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            __name__,
            # ".app",
            # ".server",
            # ".tools",
        ],
    )
    config = providers.Configuration()

    # support old extractorutils LoggingConfig (console/file)
    logging = providers.Resource(init_logging, logging_config=config.logging, deprecated_logger_config=config.logger)


class CogniteContainer(BaseContainer):
    # provides config.cognite:dict as pydantic CogniteConfig object
    # and reveals all pydantic errors on container.init_resource
    cognite_config = providers.Resource(CogniteConfig.parse_obj, obj=BaseContainer.config.cognite)

    cognite_client = providers.Factory(
        get_cognite_client,
        cognite_config,
    )


class DiagramCommandContainer(BaseContainer):
    """Container w/o 'cognite_client'

    Args:
        BaseContainer (_type_): _description_
    """

    bootstrap = providers.Resource(BootstrapCoreConfig.parse_obj, obj=BaseContainer.config.bootstrap)


class DeployCommandContainer(CogniteContainer):
    """Container providing 'cognite_client' and 'bootstrap'

    Args:
        CogniteContainer (_type_): _description_
    """

    bootstrap = providers.Resource(BootstrapCoreConfig.parse_obj, obj=CogniteContainer.config.bootstrap)


class DeleteCommandContainer(CogniteContainer):
    delete_or_deprecate = providers.Resource(
        BootstrapDeleteConfig.parse_obj, obj=BaseContainer.config.delete_or_deprecate
    )


ContainerSelector: dict[CommandMode, Type[containers.Container]] = {
    CommandMode.PREPARE: CogniteContainer,
    CommandMode.DIAGRAM: DiagramCommandContainer,
    CommandMode.DEPLOY: DeployCommandContainer,
    CommandMode.DELETE: DeleteCommandContainer,
}
