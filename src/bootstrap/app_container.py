import logging.config
import os
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
    if os.getenv("GITHUB_ACTIONS") in ("true", True):
        # if run from GITHUB_ACTIONS, the envvar is set to 'true' and the workspace-folder is mounted to
        # -v "/home/runner/work/cdf-config-hub/cdf-config-hub":"/github/workspace"
        # the buildpack image starts in the workspace-folder "/workspace",
        # which requires to extend the path to load the config
        container.config.from_yaml(Path("/github/workspace") / config_path, required=True)  # type: ignore
    else:
        container.config.from_yaml(config_path, required=True)  # type: ignore

    # TODO: inject an empty {} if not present for 'bootstrap' to trigger a default?
    # how to make this smarter in pydantic?
    # support PREPARE config.bootstrap.features.group_prefix need atm
    if "bootstrap" not in container.config():
        container.config()["bootstrap"] = {}
    logging.debug(f"{container.config()=}")

    container.init_resources()  # i.e.logging

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
    cognite_config = providers.Resource(CogniteConfig.model_validate, obj=BaseContainer.config.cognite)

    cognite_client = providers.Factory(
        get_cognite_client,
        cognite_config,
    )


class DiagramCommandContainer(BaseContainer):
    """Container w/o 'cognite_client'

    Args:
        BaseContainer (_type_): _description_
    """

    bootstrap = providers.Resource(BootstrapCoreConfig.model_validate, obj=BaseContainer.config.bootstrap)


class PrepareCommandContainer(CogniteContainer):
    bootstrap = providers.Resource(BootstrapCoreConfig.model_validate, obj=CogniteContainer.config.bootstrap)


class DeployCommandContainer(CogniteContainer):
    """Container providing 'cognite_client' and 'bootstrap'

    Args:
        CogniteContainer (_type_): _description_
    """

    bootstrap = providers.Resource(BootstrapCoreConfig.model_validate, obj=CogniteContainer.config.bootstrap)


class DeleteCommandContainer(CogniteContainer):
    delete_or_deprecate = providers.Resource(
        BootstrapDeleteConfig.model_validate, obj=BaseContainer.config.delete_or_deprecate
    )


ContainerSelector: dict[CommandMode, Type[containers.Container]] = {
    CommandMode.PREPARE: PrepareCommandContainer,
    CommandMode.DIAGRAM: DiagramCommandContainer,
    CommandMode.DEPLOY: DeployCommandContainer,
    CommandMode.DELETE: DeleteCommandContainer,
}
