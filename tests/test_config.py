from pathlib import Path

import pytest
from rich import print

from incubator.bootstrap_cli import app_container
from tests.constants import ROOT_DIRECTORY

print(ROOT_DIRECTORY)

def generate_deploy_config_01_is_valid_test_data():
    yield pytest.param(config := ROOT_DIRECTORY / "example/config-deploy-example-01.0.yml", ROOT_DIRECTORY / "../.env", id=config.name)
    yield pytest.param(config := ROOT_DIRECTORY / "example/config-deploy-example-01.1.yml", ROOT_DIRECTORY / "../.env", id=config.name)
    yield pytest.param(config := ROOT_DIRECTORY / "example/config-deploy-example-01.2.yml", ROOT_DIRECTORY / "../.env", id=config.name)
    yield pytest.param(config := ROOT_DIRECTORY / "example/config-deploy-example-01.3.yml", ROOT_DIRECTORY / "../.env", id=config.name)

@pytest.mark.parametrize("example_file, dotenv_path", generate_deploy_config_01_is_valid_test_data())
def test_deploy_config_01_is_valid(example_file: Path, dotenv_path: Path):
    """
    This test is intended to ensure that the configuration examples are valid.
    If this test fails, please update the relevant configuration example.
    """
    container: app_container.DeployCommandContainer = app_container.init_container(app_container.DeployCommandContainer, example_file, dotenv_path)

    assert container.bootstrap()
    assert container.cognite_client().config.project
    assert container.bootstrap().features


def generate_diagram_config_02_is_valid_test_data():
    yield pytest.param(config := ROOT_DIRECTORY / "example/config-diagram-example-02.0.yml", ROOT_DIRECTORY / "../.env", id=config.name)

@pytest.mark.parametrize("example_file, dotenv_path", generate_diagram_config_02_is_valid_test_data())
def test_diagram_config_02_is_valid(example_file: Path, dotenv_path: Path):
    """
    This test is intended to ensure that the configuration examples are valid.
    If this test fails, please update the relevant configuration example.
    """

    container: app_container.DiagramCommandContainer = app_container.init_container(app_container.DiagramCommandContainer, example_file, dotenv_path)

    assert container.bootstrap()

def generate_delete_config_03_is_valid_test_data():
    yield pytest.param(config := ROOT_DIRECTORY / "example/config-delete-example-03.0.yml", ROOT_DIRECTORY / "../.env", id=config.name)

@pytest.mark.parametrize("example_file, dotenv_path", generate_delete_config_03_is_valid_test_data())
def test_delete_config_03_is_valid(example_file: Path, dotenv_path: Path):
    """
    This test is intended to ensure that the configuration examples are valid.
    If this test fails, please update the relevant configuration example.
    """

    container: app_container.DeleteCommandContainer = app_container.init_container(app_container.DeleteCommandContainer, example_file, dotenv_path)

    assert container.delete_or_deprecate()

    # run 'pytest -s' to get print output in console
    print(container.delete_or_deprecate().datasets)

