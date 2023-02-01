from typing import TYPE_CHECKING, cast

from cognite.client.data_classes._base import CogniteResource, CogniteResourceList

if TYPE_CHECKING:
    from cognite.client import CogniteClient


class ModelsSpace(CogniteResource):
    """No description.
    Args:
        space (str): [1..43] The Space identifier (id). Must be unique for the resource type.
        name (str): [0..255] Human-readable name for the space.
        description (str): [0 .. 255] Used to describe the space you're defining.
        cognite_client (CogniteClient): The client to associate with this object.
    """

    def __init__(
        self,
        name: str = None,
        space: str = None,
        description: str = None,
        cognite_client: "CogniteClient" = None,
    ):
        self.space = space
        self.name = name
        self.description = description
        self._cognite_client = cast("CogniteClient", cognite_client)


class ModelsSpaceList(CogniteResourceList):
    _RESOURCE = ModelsSpace
