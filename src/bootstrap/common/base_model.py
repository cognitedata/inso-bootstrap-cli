from typing import Type

from pydantic import BaseModel, ConfigDict


def to_hyphen_case(value: str) -> str:
    """Creates alias names from Python compatible snake_case '_' to yaml typical kebap-style ('-')
    # https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/

    Args:
        value (str): the value to generate an alias for

    Returns:
        str: alias in hyphen-style
    """
    return value.replace("_", "-")


class Model(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        # generate for each field an alias in hyphen-case (kebap)
        alias_generator=to_hyphen_case,
        # an aliased field may be populated by its name as given by the model attribute, as well as the alias
        # this supports both cases to be mixed
        populate_by_name=True,
    )
    # no need for "settings_customise_sources" as we don't need any injection from envvar, dotenv, secrets
