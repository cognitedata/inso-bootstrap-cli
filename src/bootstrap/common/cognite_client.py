import logging.config
from typing import List, Optional

# TODO: PEP 484 Stub Files issue?
from cognite.client import ClientConfig, CogniteClient
from cognite.client.credentials import OAuthClientCredentials

from ..common.base_model import Model


class CogniteIdpConfig(Model):
    # fields required for OIDC client-credentials authentication
    client_name: Optional[str]
    client_id: str
    secret: str
    scopes: List[str]
    token_url: str


class CogniteConfig(Model):
    host: str
    project: str
    idp_authentication: CogniteIdpConfig

    # compatibility properties to keep get_cognite_client() in sync with other solutions
    # which are using flat-property list, no nesting and a bit different names
    @property
    def base_url(self) -> str:
        return self.host

    @property
    def token_url(self) -> str:
        return self.idp_authentication.token_url

    @property
    def scopes(self) -> List[str]:
        return self.idp_authentication.scopes

    @property
    def client_name(self) -> str:
        return self.idp_authentication.client_name or "cognite-sdk-client"

    @property
    def client_id(self) -> str:
        return self.idp_authentication.client_id

    @property
    def client_secret(self) -> str:
        return self.idp_authentication.secret


#######################
# class CogniteConfig(Model):
#     credentials: Literal["oauth"]
#     project: str = "use-case-dev"
#     client_name: Optional[str] = None
#     base_url: str
#     # all required if credentials=oauth
#     tenant_id: str
#     client_id: str
#     client_secret: str

#     @property
#     def token_url(self) -> str:
#         return f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

#     @property
#     def scopes(self) -> list[str]:
#         return [f"{self.base_url}/.default"]

#     @validator("tenant_id", "client_id", "client_secret", always=True)
#     def is_required_if_oauth(cls, value, values, field):
#         if (credentials := values.get("credentials")) and credentials == "oauth" and not value:
#             raise ValueError(f"{field.name} is required when {credentials=}")
#         return value


def get_cognite_client(cognite_config: CogniteConfig) -> CogniteClient:
    """Get an authenticated CogniteClient for the given project and user
    Returns:
        CogniteClient: The authenticated CogniteClient
    """
    try:

        logging.debug("Attempt to create CogniteClient")

        credentials = OAuthClientCredentials(
            token_url=cognite_config.token_url,
            client_id=cognite_config.client_id,
            client_secret=cognite_config.client_secret,
            scopes=cognite_config.scopes,
        )

        cnf = ClientConfig(
            client_name=cognite_config.client_name,
            base_url=cognite_config.base_url,
            project=cognite_config.project,
            credentials=credentials,
        )
        logging.debug(f"get CogniteClient for {cognite_config.project=}")

        return CogniteClient(cnf)
    except Exception as e:
        logging.critical(f"Unable to create CogniteClient: {e}")
        raise
