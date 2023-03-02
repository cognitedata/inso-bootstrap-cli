#          888                                          888
#          888                                          888
#          888                                          888
#  .d8888b 88888b.   8888b.  88888b.   .d88b.   .d88b.  888  .d88b.   .d88b.
# d88P"    888 "88b     "88b 888 "88b d88P"88b d8P  Y8b 888 d88""88b d88P"88b
# 888      888  888 .d888888 888  888 888  888 88888888 888 888  888 888  888
# Y88b.    888  888 888  888 888  888 Y88b 888 Y8b.     888 Y88..88P Y88b 888
#  "Y8888P 888  888 "Y888888 888  888  "Y88888  "Y8888  888  "Y88P"   "Y88888
#                                          888                            888
#                                     Y8b d88P                       Y8b d88P
#                                      "Y88P"                         "Y88P"
#
# 210504 mh:
#  * Adding support for minimum groups and project capabilities for read and owner groups
#  * Exception handling for root-groups to avoid duplicate groups and projects capabilities
# 210610 mh:
#  * Adding RAW DBs and datasets for groups {env}:allprojects:{owner/read} and {env}:{group}:allprojects:{owner/read}
#  * Adding functionality for updating dataset details (external id, description, etc) based on the config.yml
# 210910 pa:
#  * extended acl_default_types by labels, relationships, functions
#  * removed labels from acl_admin_types
#  * functions don't have dataset scope
# 211013 pa:
#  * renamed "adfs" to "aad" terminology => aad_mappings
#  * for AAD 'root:client' and 'root:user' can be merged into 'root'
# 211014 pa:
#  * adding new capabilities
#       extractionpipelinesAcl
#       extractionrunsAcl
# 211108 pa:
#  * adding new capabilities
#       entitymatchingAcl
#  * refactor list of acl types which only support "all" scope
#       acl_all_scope_only_types
#  * support "labels" for non admin groups
# 211110 pa:
#  * adding new capabilities
#       sessionsAcl
# 220202 pa:
#  * adding new capabilities
#       typesAcl
# 220216 pa:
#  * adding 'generate_special_groups()' to handle
#    'extractors' and 'transformations' and their 'aad_mappings'
#    * configurable through `deploy --with-special-groups=[yes|no]` parameter
#  * adding new capabilities:
#       transformationsAcl (replacing the need for magic "transformations" CDF group)
# 220404 pa:
#  * v1.4.0 limited datasets for 'owner' that they cannot edit or create datasets
#     * removed `datasets:write` capability
#     * moved that capability to action_dimensions['admin']
# 220405 sd:
#  * v1.5.0 added dry-run mode as global parameter for all commands
# 220405 pa:
#  * v1.6.0
#  * removed 'transformation' acl from 'acl_all_scope_only_types'
#     as it now supports dataset scopes too!
#  * refactor variable names to match the new documentation
#     1. group_types_dimensions > group_bootstrap_hierarchy
#     2. group_type > ns_name (namespace: src, ca, uc)
#     3. group_prefix > node_name (src:001:sap)
# 220406 pa/sd:
#  * v1.7.0
#  * added 'diagram' command which creates a Mermaid (diagram as code) output
# 220406 pa:
#  * v1.7.1
#  * started to use '# fmt:skip' to save intended multiline formatted and indented code
#    from black auto-format
# 220420 pa:
#  * v.1.9.2
#  * fixed Poetry on Windows issues
# 220422 pa:
#  * v1.10.0
#  *  issue #28 possibility to skip creation of RAW DBs
#  * added '--with-raw-capability' parameter for 'deploy' and 'diagram' commands
# 220424 pa:
#  * introduced CommandMode enums to support more detailed BootstrapCore initialization
#  * started with validation-functions ('validate_config_is_cdf_project_in_mappings')
#  * for 'diagram' command
#    - made 'cognite' section optional
#    - added support for parameter '--cdf-project' to explicit diagram a specific CDF Project
#    - Added cdf-project name to diagram "IdP groups for CDF: <>" subgraph title
#    - renamed mermaid properties from 'name/short' to 'id_name/display'
#  * documented config-deploy-example-v2.yml
# 220511 pa: v2.0.0 release :)
# 220728 pa: v2.0.3 release with replacing time.sleep() statements (which could fail to reload CDF resources in time)
#     through active caching of CDF resource changes
#     * the 'self.deployed' is now of type 'CogniteDeployedCache' with support to create, update or delete cache entries
#     Potential problem fixed with DRY-RUN and 'delete' command
#     * enhanced dry-run logging
#     Removed chunks from dataset creation (already covered by SDK)
#    * made the '--debug' flag working, which can now overwrite a INFO level from config-yaml :)
#      solution was to use the root-logger as global '_logging' variable
#      as it is shared with extractor-utils 'LoggingConfig'
# 220826 js: v2.2.0 added two more acls: templateInstances, templateGroups
#        pa: added two more acls: dataModels, dataModelInstances (for FDM), limited to "all" scope access for now
# 221121 jr: added wells capabilities to support WDL access
# 230301 pa: fix regression in lately added 'validate_config_shared_access'
#       which didn't took aggregated-node-levels into account.
#       Like `src:all` or `all` (dependent on your features.aggregated-level-name)
#       2nd fix adding `extractionConfigs` to the list of supported and scoped ACLs
#
# TODO:
#
# 220728 pa:
#   - validation step if all shared groups are covered by config
#   - atm existing datasets (not created by bootstrap) can be referenced too

import logging
from typing import Dict, Optional

import click
from click import Context
from dotenv import load_dotenv

# cli internal
from incubator.bootstrap_cli import __version__
from incubator.bootstrap_cli.app_config import CommandMode, YesNoType
from incubator.bootstrap_cli.app_exceptions import BootstrapConfigError
from incubator.bootstrap_cli.commands.delete import CommandDelete
from incubator.bootstrap_cli.commands.deploy import CommandDeploy
from incubator.bootstrap_cli.commands.diagram import CommandDiagram
from incubator.bootstrap_cli.commands.prepare import CommandPrepare

# share the root-logger, which get's later configured by extractor-utils LoggingConfig too
# that we can switch the logLevel for all logging through the '--debug' cli-flag
# 230126 pa: rename from _logger to logging
logging = logging.getLogger()


# '''
#           888 d8b          888
#           888 Y8P          888
#           888              888
#   .d8888b 888 888  .d8888b 888  888
#  d88P"    888 888 d88P"    888 .88P
#  888      888 888 888      888888K
#  Y88b.    888 888 Y88b.    888 "88b
#   "Y8888P 888 888  "Y8888P 888  888
# '''


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(prog_name="bootstrap_cli", version=__version__)
@click.option(
    "--cdf-project-name",
    help="CDF Project to interact with the CDF API, the 'BOOTSTRAP_CDF_PROJECT',"
    "environment variable can be used instead. Required for OAuth2 and optional for api-keys.",
    envvar="BOOTSTRAP_CDF_PROJECT",
)
# TODO: is cluster and alternative for host?
@click.option(
    "--cluster",
    default="westeurope-1",
    help="The CDF cluster where CDF Project is hosted (e.g. greenfield, europe-west1-1),"
    "Provide this or make sure to set the 'BOOTSTRAP_CDF_CLUSTER' environment variable. "
    "Default: westeurope-1",
    envvar="BOOTSTRAP_CDF_CLUSTER",
)
@click.option(
    "--host",
    default="https://bluefield.cognitedata.com/",
    help="The CDF host where CDF Project is hosted (e.g. https://bluefield.cognitedata.com),"
    "Provide this or make sure to set the 'BOOTSTRAP_CDF_HOST' environment variable."
    "Default: https://bluefield.cognitedata.com/",
    envvar="BOOTSTRAP_CDF_HOST",
)
# TODO: can we deprecate API_KEY option?
@click.option(
    "--api-key",
    help="API key to interact with the CDF API. Provide this or make sure to set the 'BOOTSTRAP_CDF_API_KEY',"
    "environment variable if you want to authenticate with API keys.",
    envvar="BOOTSTRAP_CDF_API_KEY",
)
@click.option(
    "--client-id",
    help="IdP client ID to interact with the CDF API. Provide this or make sure to set the "
    "'BOOTSTRAP_IDP_CLIENT_ID' environment variable if you want to authenticate with OAuth2.",
    envvar="BOOTSTRAP_IDP_CLIENT_ID",
)
@click.option(
    "--client-secret",
    help="IdP client secret to interact with the CDF API. Provide this or make sure to set the "
    "'BOOTSTRAP_IDP_CLIENT_SECRET' environment variable if you want to authenticate with OAuth2.",
    envvar="BOOTSTRAP_IDP_CLIENT_SECRET",
)
@click.option(
    "--token-url",
    help="IdP token URL to interact with the CDF API. Provide this or make sure to set the "
    "'BOOTSTRAP_IDP_TOKEN_URL' environment variable if you want to authenticate with OAuth2.",
    envvar="BOOTSTRAP_IDP_TOKEN_URL",
)
@click.option(
    "--scopes",
    help="IdP scopes to interact with the CDF API, relevant for OAuth2 authentication method. "
    "The 'BOOTSTRAP_IDP_SCOPES' environment variable can be used instead.",
    envvar="BOOTSTRAP_IDP_SCOPES",
)
@click.option(
    "--audience",
    help="IdP Audience to interact with the CDF API, relevant for OAuth2 authentication method. "
    "The 'BOOTSTRAP_IDP_AUDIENCE' environment variable can be used instead.",
    envvar="BOOTSTRAP_IDP_AUDIENCE",
)
@click.option(
    "--dotenv-path",
    help="Provide a relative or absolute path to an .env file (for command line usage only)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Print debug information",
)
@click.option(
    "--dry-run",
    default="no",
    type=click.Choice(["yes", "no"], case_sensitive=False),
    help="Log only planned CDF API actions while doing nothing." " Defaults to 'no'.",
)
@click.pass_context
def bootstrap_cli(
    # click.core.Context
    context: Context,
    # cdf
    cluster: str = "westeurope-1",
    cdf_project_name: Optional[str] = None,
    host: str = None,
    api_key: Optional[str] = None,
    # cdf idp
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    scopes: Optional[str] = None,
    token_url: Optional[str] = None,
    audience: Optional[str] = None,
    # cli
    # TODO: dotenv_path: Optional[click.Path] = None,
    dotenv_path: Optional[str] = None,
    debug: bool = False,
    dry_run: str = "no",
) -> None:

    # load .env from file if exists, use given dotenv_path if provided
    load_dotenv(dotenv_path=dotenv_path)

    context.obj = {
        # cdf
        "cluster": cluster,
        "cdf_project_name": cdf_project_name,
        "host": host,
        "api_key": api_key,
        # cdf idp
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": scopes,
        "token_url": token_url,
        "audience": audience,
        # cli
        "dotenv_path": dotenv_path,
        "debug": debug,
        "dry_run": dry_run,
    }


@click.command(help="Deploy a bootstrap configuration from a configuration file.")
@click.argument(
    "config_file",
    default="./config-bootstrap.yml",
)
@click.option(
    "--with-special-groups",
    # having this as a flag is not working for gh-action 'actions.yml' manifest
    # instead using explicit choice options
    # is_flag=True,
    # default="no",
    type=click.Choice(["yes", "no"], case_sensitive=False),
    help="Create special CDF groups, without any capabilities (extractions, transformations). Defaults to 'no'",
)
@click.option(
    "--with-raw-capability",
    # default="yes", # default defined in 'configuration.BootstrapFeatures'
    type=click.Choice(["yes", "no"], case_sensitive=False),
    help="Create RAW databases and 'rawAcl' capability. Defaults to 'yes'",
)
@click.pass_obj
def deploy(
    # click.core.Context obj
    obj: Dict,
    config_file: str,
    with_special_groups: YesNoType,
    with_raw_capability: YesNoType,
) -> None:

    click.echo(click.style("Deploying CDF Project bootstrap...", fg="red"))

    try:
        (
            CommandDeploy(config_file, command=CommandMode.DEPLOY, debug=obj["debug"])
            .validate_config_length_limits()
            .validate_config_shared_access()
            .validate_config_is_cdf_project_in_mappings()
            .dry_run(obj["dry_run"])
            .command(
                with_special_groups=with_special_groups,
                with_raw_capability=with_raw_capability,
                )
        )  # fmt:skip

        click.echo(click.style("CDF Project bootstrap deployed", fg="blue"))

    except BootstrapConfigError as e:
        exit(e.message)


@click.command(
    help="Prepares an elevated CDF group 'cdf:bootstrap', using the same AAD group link "
    "as used for the initial 'oidc-admin-group' and "
    "with additional capabilities to run the 'deploy' and 'delete' commands next. "
    "You only need to run the 'prepare' command once per CDF project."
)
@click.argument(
    "config_file",
    default="./config-bootstrap.yml",
)
@click.option(
    "--aad-source-id",
    "--idp-source-id",
    "idp_source_id",  # explicit named variable for alternatives
    required=True,
    help="Provide the IdP source ID to use for the 'cdf:bootstrap' group. "
    "Typically for a new project it's the same as configured for the initial "
    "CDF group named 'oidc-admin-group'. "
    "The parameter option '--aad-source-id' will be deprecated in next major release",
)
@click.pass_obj
def prepare(
    # click.core.Context obj
    obj: Dict,
    config_file: str,
    idp_source_id: str,
    dry_run: YesNoType = YesNoType.no,
) -> None:

    click.echo(click.style("Prepare CDF Project ...", fg="red"))

    try:
        (
            CommandPrepare(config_file, command=CommandMode.PREPARE, debug=obj["debug"])
            # .validate_config() # TODO
            .dry_run(obj["dry_run"])
            .command(idp_source_id=idp_source_id)
        )  # fmt:skip

        click.echo(click.style("CDF Project bootstrap prepared for running 'deploy' command next.", fg="blue"))

    except BootstrapConfigError as e:
        exit(e.message)


@click.command(
    help="Delete mode used to delete CDF groups, datasets and RAW databases. "
    "CDF groups and RAW databases are deleted, while datasets are archived "
    "and deprecated (datasets cannot be deleted)."
)
@click.argument(
    "config_file",
    default="./config-bootstrap.yml",
)
@click.pass_obj
def delete(
    # click.core.Context obj
    obj: Dict,
    config_file: str,
) -> None:

    click.echo(click.style("Delete CDF Project ...", fg="red"))

    try:
        (
            CommandDelete(config_file, command=CommandMode.DELETE, debug=obj["debug"])
            # .validate_config() # TODO
            .dry_run(obj["dry_run"]).command()
        )

        click.echo(
            click.style(
                "CDF Project relevant groups and raw_dbs are deleted and/or datasets are archived and deprecated ",
                fg="blue",
            )
        )

    except BootstrapConfigError as e:
        exit(e.message)


@click.command(help="Diagram mode documents the given configuration as a Mermaid diagram")
@click.argument(
    "config_file",
    default="./config-bootstrap.yml",
)
@click.option(
    "--markdown",
    default="no",
    type=click.Choice(["yes", "no"], case_sensitive=False),
    help="Encapsulate the Mermaid diagram in Markdown syntax. " "Defaults to 'no'",
)
@click.option(
    "--with-raw-capability",
    type=click.Choice(["yes", "no"], case_sensitive=False),
    help="Create RAW Databases and 'rawAcl' capability. " "Defaults to 'yes'",
)
@click.option(
    "--cdf-project",
    help="[optional] Provide the CDF project name to use for the diagram 'idp-cdf-mappings'.",
)
@click.pass_obj
def diagram(
    # click.core.Context obj
    obj: Dict,
    config_file: str,
    markdown: YesNoType,
    with_raw_capability: YesNoType,
    cdf_project: str,
) -> None:

    # click.echo(click.style("Diagram CDF Project ...", fg="red"))

    try:
        (
            CommandDiagram(config_file, command=CommandMode.DIAGRAM, debug=obj["debug"])
            .validate_config_length_limits()
            .validate_config_shared_access()
            .validate_cdf_project_available(cdf_project_from_cli=cdf_project)
            .validate_config_is_cdf_project_in_mappings(cdf_project_from_cli=cdf_project)
            # .dry_run(obj['dry_run'])
            .command(
                to_markdown=markdown,
                with_raw_capability=with_raw_capability,
                cdf_project=cdf_project,
                )
        )  # fmt:skip

        # click.echo(
        #     click.style(
        #         "CDF Project relevant groups and raw_dbs are documented as Mermaid",
        #         fg="blue",
        #     )
        # )

    except BootstrapConfigError as e:
        exit(e.message)


bootstrap_cli.add_command(deploy)
bootstrap_cli.add_command(prepare)
bootstrap_cli.add_command(delete)
bootstrap_cli.add_command(diagram)


def main() -> None:
    # call click.pass_context
    bootstrap_cli()


if __name__ == "__main__":
    main()
