import json
import logging
from collections import UserList
from collections.abc import Iterable
from typing import Any, Dict, List, Union

from cognite.client import CogniteClient, utils
from cognite.client.data_classes import Database, DataSet, Group
from cognite.client.data_classes._base import CogniteResource, CogniteResourceList

# fdm sdk injection
# v2
# from fdm_sdk_inject.data_classes.data_model_storages.spaces import DataModelStorageSpace, DataModelStorageSpaceList
# v3
from fdm_sdk_inject.data_classes.models.spaces import ModelsSpace


class CogniteResourceCache(UserList):
    """Implement own CogniteResourceList class
    To support generic code for Group, DataSet, Space and Database
    Which support simple insert, update or remove (which CogniteResourceList lacks)
    """

    # not all CDF resources support 'id' for selection, so this is the dynamic lookup for
    RESOURCE_SELECTOR_MAPPING = {
        DataSet: "id",
        Group: "id",
        Database: "name",
        # DataModelStorageSpace: "external_id",
        ModelsSpace: "space",
    }  # noqa

    def __init__(
        self,
        RESOURCE: Union[Group, Database, DataSet, ModelsSpace],
        resources: Union[CogniteResource, CogniteResourceList],
    ) -> None:
        self.RESOURCE: Union[Group, Database, DataSet, ModelsSpace] = RESOURCE
        self.SELECTOR_FIELD = CogniteResourceCache.RESOURCE_SELECTOR_MAPPING[RESOURCE]

        logging.debug(f"Init Resource Cache {RESOURCE=} with SELECTOR_FIELD='{self.SELECTOR_FIELD}'")

        # a) unpack ResourceList to simple list
        # b) is single element, pack it in list
        self.data = [r for r in resources] if isinstance(resources, CogniteResourceList) else [resources]

    def __str__(self) -> str:
        """From CogniteResourceList

        Returns:
            _type_: _description_
        """
        item = utils._time.convert_time_attributes_to_datetime(self.dump())
        return json.dumps(item, default=utils._auxiliary.json_dump_default, indent=4)

    def dump(self, camel_case: bool = False) -> List[Dict[str, Any]]:
        """Dump the instance into a json serializable Python data type.
        Args:
            camel_case (bool): Use camelCase for attribute names. Defaults to False.
        Returns:
            List[Dict[str, Any]]: A list of dicts representing the instance.
        """
        return [resource.dump(camel_case) for resource in self.data]

    def get_names(self) -> List[str]:
        """Convenience function to get list of names

        Returns:
            List[str]: _description_
        """

        def get_identifier(resource):
            """CogniteResources have different identifiers

            Args:
                resource (CogniteResource):  DataSet, Group, Database, DataModelStorageSpace (v2), ModelsSpace (v3)

            Returns:
                str: best representation we found in order 'space', 'name', 'external_id'
            """
            return (
                resource.space
                if getattr(resource, "space", False)
                else (resource.name if getattr(resource, "name", False) else resource.external_id)
            )

        return [(get_identifier(resource) or "") for resource in self.data]

    def select(self, values):
        return [c for c in self.data if getattr(c, self.SELECTOR_FIELD) in values]

    def create(self, resources: Union[CogniteResource, CogniteResourceList, List]) -> None:
        """map 'mode' to internal update function ('_' prefixed)

        Args:
            mode (CacheUpdateMode): _description_
            resources (CogniteResourceList): _description_
        """
        # handle single-element, with CogniteResourceList and List are Iterable
        resources = resources if isinstance(resources, Iterable) else [resources]
        self.data.extend([r for r in resources])

    def delete(self, resources: Union[CogniteResource, CogniteResourceList, List]) -> None:
        """Find existing resource and replace it
        a) delete
        b) call create

        Args:
            resources (CogniteResourceList): _description_
        """
        # handle single-element, with CogniteResourceList and List are Iterable
        resources = resources if isinstance(resources, Iterable) else [resources]

        # delete if exists
        matching_in_cache = self.select(values=[getattr(r, self.SELECTOR_FIELD) for r in resources])
        [self.data.remove(m) for m in matching_in_cache]

    def update(self, resources: Union[CogniteResource, CogniteResourceList, List]) -> None:
        """Find existing resource and replace it
        a) delete
        b) call create

        Args:
            resources (CogniteResourceList): _description_
        """
        # handle single-element, with CogniteResourceList and List are Iterable
        resources = resources if isinstance(resources, Iterable) else [resources]

        # delete if exists
        self.delete(resources)
        # create
        self.create(resources)


class CogniteDeployedCache:
    """Load CDF groups, datasets and RAW DBs as pd.DataFrames
    and store them in 'self.deployed' dictionary.
    """

    def __init__(self, client: CogniteClient, groups_only: bool = False):

        # init
        self.groups: CogniteResourceCache = None
        self.datasets: CogniteResourceCache = None
        self.raw_dbs: CogniteResourceCache = None
        self.spaces: CogniteResourceCache = None

        """Load CDF groups, datasets and raw databases as CogniteResourceList
        and store them in 'self.deployed' dictionary.

        Args:
            groups_only (bool, optional): Limit to CDF groups only (used by 'prepare' command). Defaults to False.
        """
        NOLIMIT = -1

        self.client: CogniteClient = client
        self.groups = CogniteResourceCache(RESOURCE=Group, resources=self.client.iam.groups.list(all=True))

        if groups_only:
            #
            # early exit
            #
            self.cache = {"groups": self.groups}
            return

        self.datasets = CogniteResourceCache(RESOURCE=DataSet, resources=self.client.data_sets.list(limit=NOLIMIT))
        self.raw_dbs = CogniteResourceCache(RESOURCE=Database, resources=self.client.raw.databases.list(limit=NOLIMIT))
        # v3
        self.spaces = CogniteResourceCache(
            RESOURCE=ModelsSpace, resources=self.client.models.spaces.list(limit=NOLIMIT)
        )
        # v2
        # self.spaces = CogniteResourceCache(
        #     RESOURCE=DataModelStorageSpace, resources=self.client.models.spaces.list(limit=NOLIMIT)
        # )

    def log_counts(self):
        logging.info(
            f"""Deployed CDF Resource counts:
            RAW Dbs({len(self.raw_dbs.get_names()) if self.raw_dbs else 'n/a with this command'})
            Data Sets({len(self.datasets.get_names()) if self.datasets else 'n/a with this command'})
            CDF Groups({len(self.groups.get_names())})
            Data Model Spaces({len(self.spaces.get_names()) if self.spaces else 'n/a with this command'})
            """
        )
