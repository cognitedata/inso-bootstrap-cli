import logging
import shutil
from enum import ReprEnum  # new in 3.11
from pathlib import Path
from typing import Any, Optional, Type

import yaml
from rich import print

from ..app_config import RoleType, ScopeCtxType, YesNoType
from .base import CommandBase


class CommandExportToCdfTk(CommandBase):
    # '''
    # TODO: figlet
    # '''

    def command(
        self,
        source_dir: Path,
        clean: bool,
        cdf_project: Optional[str] = None,
    ) -> None:
        """Export mode to create cdf-tk compatible configurations.

        Args:
            cdf_project (str, optional):
                - Provide the CDF Project to use for the diagram 'idp-cdf-mappings'.

        Example:
            # precedence over 'cognite.project' which CDF Project to diagram 'bootstrap.idp-cdf-mappings'
            # making a 'cognite' section optional
            ➟  poetry run bootstrap-cli export-to-tk --cdf-project shiny-dev configs/config-deploy-example-v2.yml | clip.exe
        """  # noqa

        # availability is validate_cdf_project_available()
        export_cdf_project = cdf_project or self.cdf_project

        # set flag to export external_ids, instead of ids
        self.with_export_to_cdftk = True

        self.cdftk_source_dir = source_dir
        is_populated = self.cdftk_source_dir.exists() and any(self.cdftk_source_dir.iterdir())
        if is_populated and clean:
            shutil.rmtree(source_dir)
            source_dir.mkdir()
            print(f"  [bold green]INFO:[/] Cleaned existing source directory {source_dir!s}.")
        elif is_populated:
            print("  [bold yellow]WARNING:[/] Source directory is not empty. Use --clean to remove existing files.")
        elif self.cdftk_source_dir.exists():
            # empty but exists
            pass
        else:
            self.cdftk_source_dir.mkdir()

        # debug new features and override with cli-parameters
        logging.info(
            f"""'export_to_cdftk' configured for
            CDF Project: <{export_cdf_project}>
            Source directory: <{self.cdftk_source_dir}>
            """
        )

        def _export_data_sets(ds: dict[str, Any]) -> None:
            """Export all datasets."""
            print("Exporting datasets", repr(ds))

            # Create folder named "data_set"
            data_set_dir = self.cdftk_source_dir / "data_sets"
            data_set_dir.mkdir(exist_ok=True)

            # Create file named "bootstrap-export.yaml" in the "data_set" folder
            file_path = data_set_dir / "bootstrap-export.yaml"

            # Use a context manager to write to the file
            with open(file_path, "w") as export_file:
                yaml.dump(ds, export_file)

        def export_item_to_cdftk(item_type: str, item_payload: list[Any]) -> None:
            """Export a single item to cdf-tk format.

            Args:
                item_type (str): Type of the item like 'rawdb', 'dataset', 'space', 'group
                item_payload (any): Name of the item like 'src:001:weather:rawdb'
            """

            match item_type:
                case "raw_dbs":
                    logging.info(f"export RAWDB: {len(item_payload)} dbs")
                case "datasets":
                    logging.info(f"export DATASET: {len(item_payload)} ds")
                    _export_data_sets(item_payload)
                case "spaces":
                    logging.info(f"export SPACE: {len(item_payload)} spc")
                case "groups":
                    logging.info(f"export GROUP: {len(item_payload)} gps")
                case _:
                    logging.error(f"Unknown item_type: {item_type=}")

        #
        # finished inline helper-methods
        # starting diagram logic
        #

        self.all_scoped_ctx = {
            # generate_target_raw_dbs -> returns a Set[str]
            ScopeCtxType.RAWDB: list(self.generate_target_raw_dbs()),  # all raw_dbs
            # generate_target_datasets -> returns a Dict[str, Any]
            ScopeCtxType.DATASET: list(self.generate_target_datasets()),  # all datasets
            ScopeCtxType.SPACE: list(self.generate_target_spaces()),  # all spaces
        }

        # process scope_ctx
        for scope_type, scopes in self.all_scoped_ctx.items():
            # logging.info(f"{scope_type=}")
            export_item_to_cdftk(scope_type.value, scopes)

        # generate all groups
        target_groups = self.generate_groups()

        export_item_to_cdftk("groups", target_groups)

        logging.info("Generated cdf-tk configs")
