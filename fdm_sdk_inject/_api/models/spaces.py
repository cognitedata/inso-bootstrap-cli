from typing import Any, Iterator, Sequence, Union, cast, overload

from cognite.client._api_client import APIClient
from requests import Response
from rich import print

from fdm_sdk_inject.data_classes.models.spaces import ModelsSpace, ModelsSpaceList

#
# HINTS: used cognite/client/_api/assets.py as template for methods
#       cognite/client/_api/transformations/jobs.py for folder-structure
#


#
# helper
#
def is_identifier_sequence(identifier):
    """Checks if parameter is list of element or string

    Args:
        identifier (str|Sequence[str]): identifier to check

    Returns:
        bool: True if it is a sequence
    """
    return isinstance(identifier, Sequence) and not isinstance(identifier, str)


class ModelsSpacesAPI(APIClient):
    _RESOURCE_PATH = "/models/spaces"
    _LIST_CLASS = ModelsSpaceList

    @property
    def url(self) -> str:
        return f"/api/v1/projects/{self._config.project}/models/spaces"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # default: 1000
        # TODO: bug: should be 1000 CDF-17519
        self._CREATE_LIMIT = 100
        self._LIST_LIMIT = 100

    def __call__(
        self,
        chunk_size: int = None,
        limit: int = None,
    ) -> Union[Iterator[ModelsSpace], Iterator[ModelsSpaceList]]:
        """Iterate over spaces
        Fetches spaces as they are iterated over, so you keep a limited number of spaces in memory.
        Args:
            chunk_size (int, optional):
                Number of spaces to return in each chunk. Defaults to yielding one data set a time.
            metadata (Dict[str, str]):
                Custom, application-specific metadata. String key -> String value.
            limit (int, optional):
                Maximum number of spaces to return. Defaults to return all items.
        Yields:
            Union[DataModelStorageSpace, DataModelStorageSpaceList]:
                yields DataModelStorageSpace one by one
                if chunk is not specified,
                else DataModelStorageSpaceList objects.
        """
        # not supported yet(?)
        # filter = None
        return self._list_generator(
            list_cls=ModelsSpaceList,
            resource_cls=ModelsSpace,
            method="POST",
            chunk_size=chunk_size,
            limit=limit,
        )

    def __iter__(self) -> Iterator[ModelsSpace]:
        """Iterate over spaces
        Fetches spaces as they are iterated over, so you keep a limited number of spaces in memory.
        Yields:
            Event: yields DataModelStorageSpace one by one.
        """
        return cast(Iterator[ModelsSpace], self())

    @overload
    def create(self, space: Sequence[ModelsSpace]) -> ModelsSpaceList:
        ...

    @overload
    def create(self, space: ModelsSpace) -> ModelsSpace:
        ...

    def create(self, space: Union[ModelsSpace, Sequence[ModelsSpace]]) -> Union[ModelsSpace, ModelsSpaceList]:
        """`Add or update (upsert) spaces. For unchanged space specifications,
        the operation completes without making any changes.
        We will not update the lastUpdatedTime value for spaces that remain unchanged.
        <https://pr-ark-codegen-1646.specs.preview.cogniteapp.com/v1.json.html#tag/Spaces-(New)/operation/ApplySpaces>`_
        Args:
            space: Union[ModelsSpace, Sequence[ModelsSpace]]: Data set or list of spaces to create.
        Returns:
            Union[ModelsSpace, ModelsSpaceList]: List of spaces
        Examples:
            Create new spaces::
                >>> from cognite.client import CogniteClient
                >>> from cognite.client.models import ModelsSpace
                >>> c = CogniteClient()
                >>> spaces = [ModelsSpace(space="1st level"), ModelsSpace(space="2nd level")]
                >>> res = c.data_model_storages.spaces.create(spaces)
        """
        return self._create_multiple(list_cls=ModelsSpaceList, resource_cls=ModelsSpace, items=space)

    def list(
        self,
        limit: int = 25,
    ) -> ModelsSpaceList:
        """List spaces
        <https://pr-ark-codegen-1646.specs.preview.cogniteapp.com/v1.json.html#tag/Spaces-(New)/operation/listSpacesV3>
        Args:
            limit (int, optional): Maximum number of spaces to return. Defaults to 10. Set to -1, float("inf") or None
                to return all items.
        Returns:
            ModelsSpaceList: List of requested spaces
        Examples:
            List spaces (no filters supported yet):
                >>> from cognite.client import CogniteClient
                >>> c = CogniteClient()
                >>> space_list = c.spaces.list(limit=5)
            Iterate over spaces:
                >>> from cognite.client import CogniteClient
                >>> c = CogniteClient()
                >>> for space in c.spaces:
                ...     space # do something with the space
            Iterate over chunks of spaces to reduce memory load::
                >>> from cognite.client import CogniteClient
                >>> c = CogniteClient()
                >>> for space_list in c.spaces(chunk_size=2500):
                ...     space_list # do something with the list
        """
        # not supported yet(?)
        # filter = None
        return self._list(list_cls=ModelsSpaceList, resource_cls=ModelsSpace, method="GET", limit=limit)

    def delete(self, space: Union[str, Sequence[str]] = None) -> None:
        """`Delete one or more spaces
        <https://pr-ark-codegen-1646.specs.preview.cogniteapp.com/v1.json.html#operation/deleteSpaces>`_
        Args:
            space (Union[str, Sequence[str]]): External ID or list of external ids
        Returns:
            None
        Examples:
            Delete spaces by external id::
                >>> from cognite.client import CogniteClient
                >>> c = CogniteClient()
                >>> c.models.spaces.delete(space="3")
        """

        # SDK FAILURE: 'space' is not suported by SDK, only 'external_id' and 'id'
        # cognite/client/utils/_identifier.py
        # self._delete_multiple(
        #     identifiers=IdentifierSequence.load(external_ids=external_id),
        #     wrap_ids=False
        # )

        # shortcut implementation from Anders
        # limit=100, non-chunking
        # https://github.com/cognitedata/tech-demo-powerops/blob/main/cognite/poweropsdemo/cdf/client_fdm_v3.py

        parameters = (
            # create an item for each elem of sequence
            {"items": [{"space": s} for s in space]}
            if is_identifier_sequence(space)
            else {"items": [{"space": space}]}  # or exactly one elem
        )

        print(f"{parameters=}")

        response: Response = self._cognite_client.post(f"{self.url}/delete", parameters)
        response.raise_for_status()

    # TODO: not tested and not used by bootstrap-cli
    # def retrieve(self, external_id: Optional[str] = None) -> Optional[ModelsSpace]:
    #     """`Retrieve a single data set by id. <https://docs.cognite.com/api/v1/#operation/getSpaces>`_
    #     Args:
    #         external_id (str, optional): External ID
    #     Returns:
    #         Optional[DataModelStorageSpace]: Requested space or None if it does not exist.
    #     Examples:
    #         Get space by external id::
    #             >>> from cognite.client import CogniteClient
    #             >>> c = CogniteClient()
    #             >>> res = c.spaces.retrieve(external_id="1")
    #     """
    #     identifiers = IdentifierSequence.load(external_ids=external_id).as_singleton()
    #     return self._retrieve_multiple(list_cls=ModelsSpaceList, resource_cls=ModelsSpace, identifiers=identifiers)

    # def retrieve_multiple(
    #     self,
    #     external_ids: Optional[Sequence[str]] = None,
    # ) -> ModelsSpaceList:
    #     """`Retrieve multiple spaces by id.
    #     <https://pr-ark-codegen-1692.specs.preview.cogniteapp.com/v1.json.html#operation/byIdsSpaces>`_
    #     Args:
    #         external_ids (Sequence[str], optional): External IDs
    #     Returns:
    #         DataModelStorageSpaceList: The requested spaces.
    #     Examples:
    #         Get spaces by external id:
    #             >>> from cognite.client import CogniteClient
    #             >>> c = CogniteClient()
    #             >>> res = c.spaces.retrieve_multiple(external_ids=["abc", "def"])
    #     """
    #     identifiers = IdentifierSequence.load(external_ids=external_ids)
    #     return self._retrieve_multiple(list_cls=ModelsSpaceList, resource_cls=ModelsSpace, identifiers=identifiers)
