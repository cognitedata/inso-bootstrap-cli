from typing import Type

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


def to_hyphen_case(value: str) -> str:
    """Creates alias names from Python compatible snake_case '_' to yaml typical kebap-style ('-')
    # https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/

    Args:
        value (str): the value to generate an alias for

    Returns:
        str: alias in hyphen-style
    """
    return value.replace("_", "-")


class Model(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        # generate for each field an alias in hyphen-case (kebap)
        alias_generator=to_hyphen_case,
        # an aliased field may be populated by its name as given by the model attribute, as well as the alias
        # this supports both cases to be mixed
        populate_by_name=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # here we choose to ignore env_settings or dotenv_settings
        # to avoid unecpectd expansion of pydantic properties matching an envvar
        # all envvar expansion exlcusivly happens in the dependency-injector
        return (init_settings,)
