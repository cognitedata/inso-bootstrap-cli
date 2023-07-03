import logging

from ..app_config import AclDefaultTypes, ScopeCtxType, YesNoType
from .base import CommandBase


class CommandDeploy(CommandBase):

    # '''
    #        .o8                       oooo
    #       "888                       `888
    #   .oooo888   .ooooo.  oo.ooooo.   888   .ooooo.  oooo    ooo
    #  d88' `888  d88' `88b  888' `88b  888  d88' `88b  `88.  .8'
    #  888   888  888ooo888  888   888  888  888   888   `88..8'
    #  888   888  888    .o  888   888  888  888   888    `888'
    #  `Y8bod88P" `Y8bod8P'  888bod8P' o888o `Y8bod8P'     .8'
    #                        888                       .o..P'
    #                       o888o                      `Y8P'
    # '''
    def command(self, with_raw_capability: YesNoType) -> None:

        # debug new features and override with cli-parameters
        logging.debug(f"From cli: {with_raw_capability=}")
        logging.debug(f"Effective: {self.with_raw_capability=}")

        # load deployed groups, datasets, raw_dbs with their ids and metadata
        logging.debug(f"RAW_DBS in CDF:\n{self.deployed.raw_dbs.get_names()}")
        logging.debug(f"DATASETS in CDF:\n{self.deployed.datasets.get_names()}")
        logging.debug(f"SPACES in CDF:\n{self.deployed.spaces.get_names()}")
        logging.debug(f"GROUPS in CDF:\n{self.deployed.groups.get_names()}")

        # run generate steps (only print results atm)

        #
        # raw_dbs
        #
        target_raw_db_names: set[str] = set()
        if self.with_raw_capability:
            target_raw_db_names, new_created_raw_db_names = self.generate_missing_raw_dbs()
            logging.info(f"All RAW_DBS from config:\n{sorted(target_raw_db_names)}")
            logging.info(f"New RAW_DBS to CDF:\n{sorted(new_created_raw_db_names)}")
        else:
            # no RAW DBs means no access to RAW at all
            # which means no 'rawAcl' capability to create
            # remove it form the default types
            logging.info("Creating no RAW_DBS and no 'rawAcl' capability")
            AclDefaultTypes.remove("raw")

        #
        # spaces
        #
        target_space_names: set[str] = set()

        if self.with_datamodel_capability:
            target_space_names, new_created_space_names = self.generate_missing_spaces()
            logging.info(f"All SPACES from config:\n{sorted(target_space_names)}")
            logging.info(f"New SPACES to CDF:\n{sorted(new_created_space_names)}")
        else:
            # no SPACESs means no access to FDM at all
            # which means no 'dataModels' and 'dataModelInstances' capabilities to create
            # remove it form the default types
            logging.info("Creating no SPACEs and no 'dataModels' and 'dataModelInstances' capabilities")
            AclDefaultTypes.remove("dataModels")
            AclDefaultTypes.remove("dataModelInstances")

        #
        # datasets
        #
        target_dataset_names, new_created_dataset_names = self.generate_missing_datasets()
        logging.info(f"All DATASETS from config:\n{sorted(target_dataset_names)}")
        logging.info(f"New DATASETS to CDF:\n{sorted(new_created_dataset_names)}")

        # store all raw_dbs and datasets in scope of this configuration
        self.all_scoped_ctx = {
            ScopeCtxType.RAWDB: list(target_raw_db_names),  # all raw_dbs
            ScopeCtxType.DATASET: list(target_dataset_names),  # all datasets
            ScopeCtxType.SPACE: list(target_space_names),  # all spaces
        }

        # CDF groups from configuration
        self.generate_groups()
        if not self.is_dry_run:
            logging.info("Created new CDF groups")

        logging.debug(f"Final RAW_DBS in CDF:\n{sorted(self.deployed.raw_dbs.get_names())}")
        logging.debug(f"Final DATASETS in CDF:\n{sorted(self.deployed.datasets.get_names())}")
        logging.debug(f"Final SPACES in CDF:\n{sorted(self.deployed.spaces.get_names())}")
        logging.debug(f"Final GROUPS in CDF\n{sorted(self.deployed.groups.get_names())}")

        # dump all configs to yaml, as cope/paste template for delete_or_deprecate step
        logging.info("Finished creating CDF Groups and required scopes (data-sets, raw-dbs, spaces)")
        self.dump_delete_template_to_yaml()
        # logging.info(f'Bootstrap Pipelines: created: {len(created)}, deleted: {len(delete_ids)}')
