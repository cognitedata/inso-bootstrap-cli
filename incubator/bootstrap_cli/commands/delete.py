import logging

from .base import CommandBase


class CommandDelete(CommandBase):
    # '''
    #        .o8            oooo                .
    #       "888            `888              .o8
    #   .oooo888   .ooooo.   888   .ooooo.  .o888oo  .ooooo.
    #  d88' `888  d88' `88b  888  d88' `88b   888   d88' `88b
    #  888   888  888ooo888  888  888ooo888   888   888ooo888
    #  888   888  888    .o  888  888    .o   888 . 888    .o
    #  `Y8bod88P" `Y8bod8P' o888o `Y8bod8P'   "888" `Y8bod8P'
    # '''
    def command(self):

        # groups
        group_names = self.delete_or_deprecate.groups
        if group_names:
            delete_group_ids = [g.id for g in self.deployed.groups if g.name in group_names]
            if delete_group_ids:
                # only delete groups which exist
                logging.info(f"DELETE groups: {group_names}")
                if self.is_dry_run:
                    logging.info(f"Dry run - Deleting groups: <{group_names}>")
                else:
                    self.client.iam.groups.delete(delete_group_ids)
                    self.deployed.groups.delete(resources=self.deployed.groups.select(values=delete_group_ids))

            else:
                logging.info(f"Groups already deleted: {group_names}")
        else:
            logging.info("No groups to delete")

        # spaces
        space_names = self.delete_or_deprecate.spaces
        if space_names:
            # v2 spaces have 'external_id' only
            # delete_space_ids = [s.external_id for s in self.deployed.spaces if s.external_id in space_names]
            # v3 spaces have 'space' not 'external_id'
            delete_space_ids = [s.space for s in self.deployed.spaces if s.space in space_names]
            if delete_space_ids:
                # only delete space which exist
                logging.info(f"DELETE spaces: {space_names}")
                if self.is_dry_run:
                    logging.info(f"Dry run - Deleting spaces: <{space_names}>")
                else:
                    # TODO: delete is not supported in v2 only v3
                    self.client.models.spaces.delete(delete_space_ids)
                    self.deployed.spaces.delete(resources=self.deployed.spaces.select(values=delete_space_ids))

            else:
                logging.info(f"Spaces already deleted: {space_names}")
        else:
            logging.info("No spaces to delete")

        # raw_dbs
        raw_db_names = self.delete_or_deprecate.raw_dbs
        if raw_db_names:
            delete_raw_db_names = list(set(raw_db_names).intersection(set(self.deployed.raw_dbs.get_names())))
            if delete_raw_db_names:
                # only delete dbs which exist
                # print("DELETE raw_dbs recursive with tables: ", raw_db_names)
                logging.info(f"DELETE raw_dbs recursive with tables: {raw_db_names}")
                if self.is_dry_run:
                    logging.info(f"Dry run - Deprecating raw_dbs: <{raw_db_names}>")
                else:
                    self.client.raw.databases.delete(delete_raw_db_names, recursive=True)
                    self.deployed.raw_dbs.delete(resources=self.deployed.raw_dbs.select(values=delete_raw_db_names))
            else:
                # print(f"RAW DBs already deleted: {raw_db_names}")
                logging.info(f"RAW DBs already deleted: {raw_db_names}")
        else:
            logging.info("No RAW Databases to delete")

        # datasets cannot be deleted by design
        # deprecate/archive them by prefix name with "_DEPR_", setting
        # "archive=true" and a "description" with timestamp of deprecation
        dataset_names = self.delete_or_deprecate.datasets
        if dataset_names:
            # get datasets which exists by name
            delete_datasets = [ds for ds in self.deployed.datasets if ds.name in dataset_names]
            if delete_datasets:
                for ds in delete_datasets:
                    logging.info(f"DEPRECATE dataset: {ds.name}")
                    update_dataset = self.client.data_sets.retrieve(id=ds.id)
                    update_dataset.name = (
                        f"_DEPR_{update_dataset.name}"
                        if not update_dataset.name.startswith("_DEPR_")
                        else f"{update_dataset.name}"
                    )  # don't stack the DEPR prefixes
                    update_dataset.description = "Deprecated {}".format(self.get_timestamp())
                    update_dataset.metadata = dict(update_dataset.metadata, archived=True)  # or dict(a, **b)
                    update_dataset.external_id = f"_DEPR_{update_dataset.external_id}_[{self.get_timestamp()}]"
                    if self.is_dry_run:
                        logging.info(f"Dry run - Deprecated dataset details: <{update_dataset}>")
                    else:
                        updated_datasets = self.client.data_sets.update(update_dataset)
                        self.deployed.datasets.update(resources=updated_datasets)

        else:
            logging.info("No datasets to archive (and mark as deprecated)")

        # dump all configs to yaml, as cope/paste template for delete_or_deprecate step
        logging.info("Finished deleting CDF groups, datasets and RAW Databases")
        self.dump_delete_template_to_yaml()
        # TODO: write to file or standard output
        logging.info("Finished deleting CDF groups, datasets and RAW Databases")
