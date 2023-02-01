from typing import Any

from cognite.client._api_client import APIClient

# from cognite.client._api.data_model_storages.spaces import DataModelStorageSpacesAPI
from fdm_sdk_inject._api.models.spaces import ModelsSpacesAPI

# from cognite.client.data_classes.data_model_storages.spaces import (
# from fdm_sdk_inject.data_classes.models.spaces import (
#     ModelsSpace,
#     ModelsSpaceList
#     )


class ModelsAPI(APIClient):
    _RESOURCE_PATH = "/models"
    # _LIST_CLASS = DataModelStorageList

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.spaces = ModelsSpacesAPI(*args, **kwargs)
        # other modules according to <https://pr-ark-codegen-1692.specs.preview.cogniteapp.com/v1.json.html#tag/Data-Model-Storage-API>
        # self.modules = DataModelStorageModulesAPI(*args, **kwargs)
        # self.nodes = DataModelStorageNodesAPI(*args, **kwargs)
        # self.edges = DataModelStorageEdgesAPI(*args, **kwargs)
        # self.graphqueries = DataModelStorageGraphQueriesAPI(*args, **kwargs)
