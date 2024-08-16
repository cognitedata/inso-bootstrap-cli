from typing import Optional
import itertools

from pydantic import model_validator
from .common.base_model import Model
from rich import print as rprint


class Rawdb(Model):
    name: str


class Space(Model):
    name: str


class Dataset(Model):
    name: str


class ActionSet(Model):
    name: str
    description: str
    action_mapping: dict[str, list[str]] = {}


class AclSet(Model):
    name: str
    description: str = ""
    compose: Optional[list[str]] = []
    exclude: Optional[list[str]] = []
    explicit: Optional[list[str]] = []


class ExplicitScopes(Model):
    rawdbs: Optional[list[Rawdb]] = []
    spaces: Optional[list[Space]] = []
    datasets: Optional[list[Dataset]] = []


class ScopeSet(Model):
    name: str
    description: str = ""
    all_scope: Optional[bool] = False
    compose: Optional[list[str]] = []
    exclude: Optional[list[str]] = []
    explicit: Optional[ExplicitScopes] = []


class Capability(Model):
    acls: list[str]
    scopes: list[str]
    actions: list[str]


class CapabilitySet(Model):
    name: str
    description: str
    compose: Optional[list[str]] = []
    exclude: Optional[list[str]] = []
    capabilities: list[Capability] = []


class Group(Model):
    name: str
    capability_sets: list[str]
    metadata: Optional[dict[str, str]] = {}
    sourceId: str


class IdpCdfMapping(Model):
    project: str
    groups: list[Group]


class Config(Model):
    idp_cdf_mapping: list[IdpCdfMapping]
    action_sets: list[ActionSet]
    acl_sets: list[AclSet]
    scope_sets: list[ScopeSet]
    capability_sets: list[CapabilitySet]

    @model_validator(mode="after")
    def validate_compose(self, info):
        """validate loaded config
        1. get all declared names
        2. scope-set self-references are valid
        3. acl-set self-references are valid
        4. capability-set self-references valid
        5. capability-set references to acls, scopes and actions are valid
        6. capability-set references in groups are valid
        """

        # 1. get declared names
        scope_set_names = [s.name for s in self.scope_sets]
        acl_set_names = [s.name for s in self.acl_sets]
        acl_set_supported_names = set(acl_set_names) | set(itertools.chain(*[s.explicit for s in self.acl_sets]))
        action_set_names = [s.name for s in self.action_sets]
        capability_set_names = [s.name for s in self.capability_sets]

        rprint(
            f"scope_set_names: {sorted(scope_set_names)}\n"
            f"acl_set_names: {sorted(acl_set_names)}\n"
            f"acl_set_supported_names: {sorted(acl_set_supported_names)}\n"
            f"action_set_names: {sorted(action_set_names)}\n"
            f"capability_set_names: {sorted(capability_set_names)}\n"
        )

        # 2. acl-set self-references are valid
        for acl_set in self.acl_sets:
            if acl_set.compose:
                for compose_name in acl_set.compose:
                    if compose_name not in acl_set_supported_names:
                        raise ValueError(
                            f"Invalid SetScope compose name: '{compose_name}' used in acl: '{acl_set.name}'"
                        )
            if acl_set.exclude:
                for exclude_name in acl_set.exclude:
                    if exclude_name not in acl_set_supported_names:
                        raise ValueError(
                            f"Invalid SetScope exclude name: '{exclude_name}' used in acl: '{acl_set.name}'"
                        )

        # 3. scope-set self-references are valid
        for scope_set in self.scope_sets:
            if scope_set.compose:
                for compose_name in scope_set.compose:
                    if compose_name not in scope_set_names:
                        raise ValueError(
                            f"Invalid SetScope compose name: '{compose_name}' used in scope: '{scope_set.name}'"
                        )
            if scope_set.exclude:
                for exclude_name in scope_set.exclude:
                    if exclude_name not in scope_set_names:
                        raise ValueError(
                            f"Invalid SetScope exclude name: '{exclude_name}' used in scope: '{scope_set.name}'"
                        )

        # 4. capability-set self-references valid
        for capability_set in self.capability_sets:
            if capability_set.compose:
                for compose_name in capability_set.compose:
                    if compose_name not in capability_set_names:
                        raise ValueError(
                            f"Invalid SetScope compose name: '{compose_name}' used in capabilty: '{capability_set.name}'"
                        )
            if capability_set.exclude:
                for exclude_name in capability_set.exclude:
                    if exclude_name not in capability_set_names:
                        raise ValueError(
                            f"Invalid SetScope exclude name: '{exclude_name}' used in capabilty: '{capability_set.name}'"
                        )

        # 5. capability-set references to acls, scopes and actions are valid
        for capability_set in self.capability_sets:
            for capability in capability_set.capabilities:
                for acl_name in capability.acls:
                    if acl_name not in acl_set_supported_names:
                        raise ValueError(f"Invalid ACL name: '{acl_name}' used in capabilty: '{capability_set.name}'")
                for scope_name in capability.scopes:
                    if scope_name not in scope_set_names:
                        raise ValueError(
                            f"Invalid Scope name: '{scope_name}' used in capabilty: '{capability_set.name}'"
                        )
                for action_name in capability.actions:
                    if action_name not in action_set_names:
                        raise ValueError(
                            f"Invalid Action name: '{action_name}' used in capabilty: '{capability_set.name}'"
                        )

        # 6. capability-set references in groups are valid
        for idp_cdf_mapping in self.idp_cdf_mapping:
            for group in idp_cdf_mapping.groups:
                for capability_set_name in group.capability_sets:
                    if capability_set_name not in capability_set_names:
                        raise ValueError(
                            f"Invalid CapabilitySet name: '{capability_set_name}' used in group: '{group.name}'"
                        )

        return self


# Example usage:
if __name__ == "__main__":
    from pathlib import Path
    import yaml

    # Get the path of the current script
    current_script_path = Path(__file__).resolve().parent

    #
    yaml_file = current_script_path / "config/240816-v4-tk-config-sketch.yml"
    config_data = yaml.safe_load(yaml_file.read_text())
    config = Config(**config_data)

    rprint(config.model_dump())
