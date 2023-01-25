import logging.config
from pathlib import Path
from typing import Any, Dict, Optional

from cognite.client import ClientConfig, CogniteClient
from cognite.client.credentials import OAuthClientCredentials
from dependency_injector import containers, providers
from dotenv import load_dotenv
from rich import print

from .app_config import (
    CogniteConfig,
    BootstrapCoreConfig,
    BootstrapDeleteConfig,
    )

def init_container(container_cls: containers.Container, config_path: str | Path = "/etc/f25e/config.yaml", dotenv_path: str | Path = None):
    """Spinning up container and 

    Args:
        container_cls (containers.Container): support different
        config_path (str | Path, optional): _description_. Defaults to "/etc/f25e/config.yaml".
        dotenv_path (str | Path, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    # if .env file exists, load it and override existing env-variables
    load_dotenv(dotenv_path, override=True)

    container = container_cls()
    container.config.from_yaml(config_path, required=True)

    logging.debug(f"{container.config()=}")

    container.init_resources()  # i.e.logging
    return container


def init_logging(config: Optional[Dict]):
    if config:
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)

    yield logging.getLogger()


def shutdown_container(container):
    logging.debug("function to handle additional shutdown of resources")
    container.shutdown_resources()


def get_cognite_client(cognite_config: CogniteConfig) -> CogniteClient:
    """Get an authenticated CogniteClient for the given project and user
    Returns:
        CogniteClient: The authenticated CogniteClient
    """
    try:
        logging.debug("Attempt to create CogniteClient")

        credentials = OAuthClientCredentials(
            token_url=cognite_config.token_url,
            client_id=cognite_config.client_id,
            client_secret=cognite_config.client_secret,
            scopes=cognite_config.scopes,
        )
        default_client_name = "developer_client"

        cnf = ClientConfig(
            client_name=cognite_config.client_name or default_client_name,
            base_url=cognite_config.base_url,
            project=cognite_config.project,
            credentials=credentials,
        )
        logging.debug(f"get CogniteClient for {cognite_config.project=}")
        return CogniteClient(cnf)
    except Exception as e:
        logging.critical(f"Unable to create CogniteClient: {e}")
        raise

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

    logging = providers.Resource(init_logging, config=config.logging)

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
    delete_or_deprecate = providers.Resource(BootstrapDeleteConfig.parse_obj, obj=BaseContainer.config.delete_or_deprecate)
