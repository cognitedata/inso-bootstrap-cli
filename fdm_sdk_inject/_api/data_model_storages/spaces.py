from typing import Any, Iterator, Optional, Sequence, Union, cast, overload

from cognite.client._api_client import APIClient
from cognite.client.utils._identifier import IdentifierSequence

from fdm_sdk_inject.data_classes.data_model_storages.spaces import DataModelStorageSpace, DataModelStorageSpaceList

#
# HINTS: used cognite/client/_api/assets.py as template for methods
#       cognite/client/_api/transformations/jobs.py for folder-structure
#


class DataModelStorageSpacesAPI(APIClient):
    _RESOURCE_PATH = "/datamodelstorage/spaces"
    _LIST_CLASS = DataModelStorageSpaceList

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # default: 1000
        # TODO: still 100?
        self._CREATE_LIMIT = 100

    def __call__(
        self,
        chunk_size: int = None,
        limit: int = None,
    ) -> Union[Iterator[DataModelStorageSpace], Iterator[DataModelStorageSpaceList]]:
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
                yields DataModelStorageSpace one by one if chunk is not specified,
                else DataModelStorageSpaceList objects.
        """
        # not supported yet(?)
        # filter = None
        return self._list_generator(
            list_cls=DataModelStorageSpaceList,
            resource_cls=DataModelStorageSpace,
            method="POST",
            chunk_size=chunk_size,
            limit=limit,
        )

    def __iter__(self) -> Iterator[DataModelStorageSpace]:
        """Iterate over spaces
        Fetches spaces as they are iterated over, so you keep a limited number of spaces in memory.
        Yields:
            Event: yields DataModelStorageSpace one by one.
        """
        return cast(Iterator[DataModelStorageSpace], self())

    @overload
    def create(self, space: Sequence[DataModelStorageSpace]) -> DataModelStorageSpaceList:
        ...

    @overload
    def create(self, space: DataModelStorageSpace) -> DataModelStorageSpace:
        ...

    def create(
        self, space: Union[DataModelStorageSpace, Sequence[DataModelStorageSpace]]
    ) -> Union[DataModelStorageSpace, DataModelStorageSpaceList]:
        """`Create one or more spaces. <https://docs.cognite.com/api/v1/#operation/createSpaces>`_
        Args:
            space: Union[DataModelStorageSpace, Sequence[DataModelStorageSpace]]: Data set or list of spaces to create.
        Returns:
            Union[DataModelStorageSpace, DataModelStorageSpaceList]: Created data set(s)
        Examples:
            Create new spaces::
                >>> from cognite.client import CogniteClient
                >>> from cognite.client.data_model_storage import DataModelStorageSpace
                >>> c = CogniteClient()
                >>> spaces = [DataModelStorageSpace(external_id="1st level"), DataModelStorageSpace(external_id="2nd level")]
                >>> res = c.data_model_storages.spaces.create(spaces)
        """
        return self._create_multiple(
            list_cls=DataModelStorageSpaceList, resource_cls=DataModelStorageSpace, items=space
        )

    def retrieve(self, external_id: Optional[str] = None) -> Optional[DataModelStorageSpace]:
        """`Retrieve a single data set by id. <https://docs.cognite.com/api/v1/#operation/getSpaces>`_
        Args:
            external_id (str, optional): External ID
        Returns:
            Optional[DataModelStorageSpace]: Requested space or None if it does not exist.
        Examples:
            Get space by external id::
                >>> from cognite.client import CogniteClient
                >>> c = CogniteClient()
                >>> res = c.spaces.retrieve(external_id="1")
        """
        identifiers = IdentifierSequence.load(external_ids=external_id).as_singleton()
        return self._retrieve_multiple(
            list_cls=DataModelStorageSpaceList, resource_cls=DataModelStorageSpace, identifiers=identifiers
        )

    def retrieve_multiple(
        self,
        external_ids: Optional[Sequence[str]] = None,
    ) -> DataModelStorageSpaceList:
        """`Retrieve multiple spaces by id. <https://pr-ark-codegen-1692.specs.preview.cogniteapp.com/v1.json.html#operation/byIdsSpaces>`_
        Args:
            external_ids (Sequence[str], optional): External IDs
        Returns:
            DataModelStorageSpaceList: The requested spaces.
        Examples:
            Get spaces by external id::
                >>> from cognite.client import CogniteClient
                >>> c = CogniteClient()
                >>> res = c.spaces.retrieve_multiple(external_ids=["abc", "def"])
        """
        identifiers = IdentifierSequence.load(external_ids=external_ids)
        return self._retrieve_multiple(
            list_cls=DataModelStorageSpaceList, resource_cls=DataModelStorageSpace, identifiers=identifiers
        )

    def list(
        self,
        limit: int = 25,
    ) -> DataModelStorageSpaceList:
        """`List spaces <https://pr-ark-codegen-1692.specs.preview.cogniteapp.com/v1.json.html#operation/listSpaces>`_
        Args:
            limit (int, optional): Maximum number of spaces to return. Defaults to 25. Set to -1, float("inf") or None
                to return all items.
        Returns:
            DataModelStorageSpaceList: List of requested spaces
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
        return self._list(
            list_cls=DataModelStorageSpaceList, resource_cls=DataModelStorageSpace, method="POST", limit=limit
        )

    def delete(self, external_id: Union[str, Sequence[str]] = None) -> None:
        """`Delete one or more spaces 
        <https://pr-ark-codegen-1692.specs.preview.cogniteapp.com/v1.json.html#operation/deleteSpaces>`_
        Args:
            external_id (Union[str, Sequence[str]]): External ID or list of external ids
        Returns:
            None
        Examples:
            Delete spaces by external id::
                >>> from cognite.client import CogniteClient
                >>> c = CogniteClient()
                >>> c.data_model_storages.spaces.delete(external_id="3")
        """
        # FAILURE: SDK Identifier and IdentifierSequence cannot handle 'spaces' only `external_id' or 'id'
        # self._delete_multiple(
        #     identifiers=IdentifierSequence.load(external_ids=external_id),
        #     wrap_ids=False
        # )

    # not supported yet(?)
    # def update(..)
