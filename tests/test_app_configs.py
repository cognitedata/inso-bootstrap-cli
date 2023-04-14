from pathlib import Path

import pytest
from rich import print

from bootstrap.app_config import CommandMode
from bootstrap.app_container import (  # PrepareCommandContainer,
    ContainerSelector,
    DeleteCommandContainer,
    DeployCommandContainer,
    DiagramCommandContainer,
    init_container,
)
from tests.constants import ROOT_DIRECTORY

print(ROOT_DIRECTORY)


def generate_deploy_config_01_is_valid_test_data():
    yield pytest.param(
        config := ROOT_DIRECTORY / "example/config-deploy-example-01.0.yml",
        ROOT_DIRECTORY / "example/.env_mock",
        id=config.name,
    )
    yield pytest.param(
        config := ROOT_DIRECTORY / "example/config-deploy-example-01.1.yml",
        ROOT_DIRECTORY / "example/.env_mock",
        id=config.name,
    )
    yield pytest.param(
        config := ROOT_DIRECTORY / "example/config-deploy-example-01.2.yml",
        ROOT_DIRECTORY / "example/.env_mock",
        id=config.name,
    )
    yield pytest.param(
        config := ROOT_DIRECTORY / "example/config-deploy-example-01.3.yml",
        ROOT_DIRECTORY / "example/.env_mock",
        id=config.name,
    )


@pytest.mark.parametrize("example_file, dotenv_path", generate_deploy_config_01_is_valid_test_data())
def test_deploy_config_01_is_valid(example_file: Path, dotenv_path: Path):
    """
    This test is intended to ensure that the configuration examples are valid.
    If this test fails, please update the relevant configuration example.
    """
    ContainerCls = ContainerSelector[CommandMode.DEPLOY]
    container: DeployCommandContainer = init_container(ContainerCls, example_file, dotenv_path)

    # must contain bootstrap section
    assert container.bootstrap()
    assert isinstance(container.bootstrap().features.with_raw_capability, bool)
    assert isinstance(container.bootstrap().idp_cdf_mappings, list)
    assert isinstance(container.bootstrap().namespaces, list)
    # must be able to instantiate a CogniteClient (even with mocked client/secret)
    assert container.cognite_client().config.project


def generate_diagram_config_02_is_valid_test_data():
    yield pytest.param(
        config := ROOT_DIRECTORY / "example/config-diagram-example-02.0.yml", ROOT_DIRECTORY / "../.env", id=config.name
    )


@pytest.mark.parametrize("example_file, dotenv_path", generate_diagram_config_02_is_valid_test_data())
def test_diagram_config_02_is_valid(example_file: Path, dotenv_path: Path):
    """
    This test is intended to ensure that the configuration examples are valid.
    If this test fails, please update the relevant configuration example.
    """

    ContainerCls = ContainerSelector[CommandMode.DIAGRAM]
    container: DiagramCommandContainer = init_container(ContainerCls, example_file, dotenv_path)

    assert container.bootstrap()


def generate_delete_config_03_is_valid_test_data():
    yield pytest.param(
        config := ROOT_DIRECTORY / "example/config-delete-example-03.0.yml", ROOT_DIRECTORY / "../.env", id=config.name
    )


@pytest.mark.parametrize("example_file, dotenv_path", generate_delete_config_03_is_valid_test_data())
def test_delete_config_03_is_valid(example_file: Path, dotenv_path: Path):
    """
    This test is intended to ensure that the configuration examples are valid.
    If this test fails, please update the relevant configuration example.
    """

    ContainerCls = ContainerSelector[CommandMode.DELETE]
    container: DeleteCommandContainer = init_container(ContainerCls, example_file, dotenv_path)

    assert container.delete_or_deprecate()
    assert isinstance(container.delete_or_deprecate().datasets, list)
    assert isinstance(container.delete_or_deprecate().groups, list)
    assert isinstance(container.delete_or_deprecate().raw_dbs, list)

    # must be able to instantiate a CogniteClient (even with mocked client/secret)
    assert container.cognite_client().config.project
