import logging

from .base import BootstrapCommandBase


class BootstrapPrepare(BootstrapCommandBase):
    # '''
    #  oo.ooooo.  oooo d8b  .ooooo.  oo.ooooo.   .oooo.   oooo d8b  .ooooo.
    #   888' `88b `888""8P d88' `88b  888' `88b `P  )88b  `888""8P d88' `88b
    #   888   888  888     888ooo888  888   888  .oP"888   888     888ooo888
    #   888   888  888     888    .o  888   888 d8(  888   888     888    .o
    #   888bod8P' d888b    `Y8bod8P'  888bod8P' `Y888""8o d888b    `Y8bod8P'
    #   888                           888
    #  o888o                         o888o
    # '''
    def command(self, idp_source_id: str) -> None:
        group_name = "cdf:bootstrap"
        # group_name = f"{create_config.environment}:bootstrap"

        group_capabilities = [
            {"datasetsAcl": {"actions": ["READ", "WRITE", "OWNER"], "scope": {"all": {}}}},
            {"rawAcl": {"actions": ["READ", "WRITE", "LIST"], "scope": {"all": {}}}},
            # DMS v2+v3 compatible data-modelling fdm scope
            {"dataModelsAcl": {"actions": ["READ", "WRITE"], "scope": {"all": {}}}},
            {"groupsAcl": {"actions": ["LIST", "READ", "CREATE", "UPDATE", "DELETE"], "scope": {"all": {}}}},
            {"projectsAcl": {"actions": ["READ", "UPDATE"], "scope": {"all": {}}}},
        ]

        # TODO: replace with dataclass
        idp_mapping = [
            # sourceId
            idp_source_id,
            # sourceName
            f"IdP group ID: {idp_source_id}",
        ]

        logging.debug(f"GROUPS in CDF:\n{self.deployed.groups}")

        if self.is_dry_run:
            logging.info(f"Dry run - Creating minimum CDF Group for bootstrap: <{group_name=}> with {idp_mapping=}")
        else:
            # allows idempotent creates, as it cleans up old groups with same names after creation
            self.create_group(group_name=group_name, group_capabilities=group_capabilities, idp_mapping=idp_mapping)
            logging.info(f"Created CDF group {group_name}")

        logging.info("Finished CDF Project Bootstrapper in 'prepare' mode ")
