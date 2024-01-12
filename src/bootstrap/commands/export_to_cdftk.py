import logging
import re
import shutil
from enum import ReprEnum  # new in 3.11
from pathlib import Path
from typing import Any, Optional, Type, cast

import yaml

# from sdk v7.13.2
from cognite.client.utils._text import convert_all_keys_recursive
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

        # def dump(output: dict[str, Any], camel_case: bool = True) -> dict[str, Any]:
        #     """from sdk v7.13.2

        #     Args:
        #         output (dict[str, Any]): _description_
        #         camel_case (bool, optional): _description_. Defaults to True.

        #     Returns:
        #         dict[str, Any]: _description_
        #     """
        #     if camel_case:
        #         output = convert_all_keys_recursive(output)
        #     return output

        def _export_raw_dbs(rs: set[str]) -> None:
            """Export all rawdbs.
            Folder must be named "raw"
            File suffix must be ".yaml"
            """
            # print("Exporting rawdbs", repr(rs))

            # Create folder named "raw"
            data_set_dir = self.cdftk_source_dir / "raw"
            data_set_dir.mkdir(exist_ok=True)

            file_path = data_set_dir / "rawdb-array-export.yaml"

            # Use a context manager to write to the file
            with open(file_path, "w") as export_file:
                yaml.dump([dict(dbName=r) for r in rs], export_file)

        def _export_spaces(spcs: set[str]) -> None:
            """Export all spaces.
            Folder must be named "data_models"
            File suffix must be ".space.yaml"
            """
            # print("Exporting spaces", repr(spcs))

            # Create folder named "data_models"
            data_set_dir = self.cdftk_source_dir / "data_models"
            data_set_dir.mkdir(exist_ok=True)

            file_path = data_set_dir / "spc-array-export.space.yaml"

            # Use a context manager to write to the file
            with open(file_path, "w") as export_file:
                yaml.dump([dict(space=spc) for spc in spcs], export_file)

        def _export_data_sets(ds: dict[str, Any]) -> None:
            """Export all datasets.
            Folder must be named "data_set"
            File suffix must be ".yaml"
            """
            # print("Exporting datasets", repr(ds))

            # Create folder named "data_set"
            data_set_dir = self.cdftk_source_dir / "data_sets"
            data_set_dir.mkdir(exist_ok=True)

            # Create file named "bootstrap-export.yaml" in the "data_set" folder
            file_path = data_set_dir / "ds-array-export.yaml"

            # transform
            # Replace key 'external_id' with 'externalId'
            ds = {k.replace("external_id", "externalId"): v for k, v in ds.items()}

            ds_flat = [
                # use a dict comprehension to rename the key in 'v'
                # and add the key 'name' with the value of 'k'
                dict(name=k, **{_k.replace("external_id", "externalId"): _v for _k, _v in v.items()})
                for k, v in ds.items()
            ]

            # Use a context manager to write to the file
            with open(file_path, "w") as export_file:
                yaml.dump(ds_flat, export_file)

        def _export_groups(grps: dict[str, Any]) -> None:
            """Export all groups.
            Folder must be named "auth"
            File suffix must be ".yaml"
            """
            # print("Exporting groups", repr(grps))

            # Create folder named "auth"
            data_set_dir = self.cdftk_source_dir / "auth"
            data_set_dir.mkdir(exist_ok=True)

            # Create file named "bootstrap-export.yaml" in the "data_set" folder
            file_path = data_set_dir / "grp-array-export.yaml"

            # Use a context manager to write to the file
            with open(file_path, "w") as export_file:
                # try to get the easydict out again
                yaml.dump(grps, export_file)

        def export_item_to_cdftk(item_type: str, item_payload: set | dict[str, Any]) -> None:
            """Export a single item to cdf-tk format.

            Args:
                item_type (str): Type of the item like 'rawdb', 'dataset', 'space', 'group
                item_payload (any): Name of the item like 'src:001:weather:rawdb'
            """

            match item_type:
                case "raw_dbs":
                    logging.info(f"export RAWDB: {len(item_payload)} dbs")
                    _export_raw_dbs(item_payload)
                case "datasets":
                    logging.info(f"export DATASET: {len(item_payload)} ds")
                    _export_data_sets(item_payload)
                case "spaces":
                    logging.info(f"export SPACE: {len(item_payload)} spc")
                    _export_spaces(item_payload)
                case "groups":
                    logging.info(f"export GROUP: {len(item_payload)} gps")
                    _export_groups(item_payload)
                case _:
                    logging.error(f"Unknown item_type: {item_type=}")

        #
        # finished inline helper-methods
        # starting diagram logic
        #

        # required to pls some internals
        self.all_scoped_ctx = {
            # generate_target_raw_dbs -> returns a Set[str]
            ScopeCtxType.RAWDB: list(self.generate_target_raw_dbs()),  # all raw_dbs
            # generate_target_datasets -> returns a Dict[str, Any]
            ScopeCtxType.DATASET: list(self.generate_target_datasets()),  # all datasets
            ScopeCtxType.SPACE: list(self.generate_target_spaces()),  # all spaces
        }

        # process scope_ctx
        export_item_to_cdftk(ScopeCtxType.RAWDB, self.generate_target_raw_dbs())
        export_item_to_cdftk(ScopeCtxType.DATASET, self.generate_target_datasets())
        export_item_to_cdftk(ScopeCtxType.SPACE, self.generate_target_spaces())

        # generate all groups
        target_groups = self.generate_groups()

        export_item_to_cdftk("groups", target_groups)

        logging.info("Generated cdf-tk configs")
