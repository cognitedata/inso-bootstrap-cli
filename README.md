# CDF Project Bootstrap

Configuration driven bootstrap of CDF Groups, Datasets, RAW Databases with data separation on
sources, use-case and user-input level. Allowing (configurable) shared-access between each other for the solutions (like server-applications) running transformations or use-cases.

## Table of Content
<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

<!-- code_chunk_output -->

- [Bootstrap-cli](#bootstrap-cli)
  - [Table of Content](#table-of-content)
  - [Bootstrap Run Modes](#bootstrap-run-modes)
    - [Prepare Mode](#prepare-mode)
    - [Create Mode](#create-mode)
    - [Delete Mode](#delete-mode)
  - [Configuration](#configuration)
      - [Configuration for All Modes](#configuration-for-all-modes)
      - [Configuration for Create Mode](#configuration-for-create-mode)
        - [Environment](#environment)
        - [Prefix External IDs](#prefix-external-ids)
        - [Adfs-links](#adfs-links)
        - [Bootstrap](#bootstrap)
      - [Configuration for Delete Mode](#configuration-for-delete-mode)
        - [Delete_or_deprecate](#delete_or_deprecate)
  - [Development](#development)
    - [How To Run](#how-to-run)
  - [End-result after Bootstrapping the CDF Tenant](#end-result-after-bootstrapping-the-cdf-tenant)
    - [Per Facility, Corporate Application and Use Case](#per-facility-corporate-application-and-use-case)
    - [CDF Groups](#cdf-groups)
    - [Raw DBs](#raw-dbs)
    - [Datasets](#datasets)
  - [High-level CDF Groups, RAW DBs and Datasets](#high-level-cdf-groups-raw-dbs-and-datasets)
    - [For all Facilities](#for-all-facilities)
    - [For all Corporate Applications](#for-all-corporate-applications)
    - [For all Use Cases](#for-all-use-cases)
    - [For all Three](#for-all-three)
    - [Root User](#root-user)

## Bootstrap Run Modes

### Prepare Mode

The very first time the Bootstrap code should be executed on a new CDF project, this code must run in `prepare` mode.
The initial "admin" group that comes with a CDF project only covers these ACLs:

- `projects`
- `groups`

For bootstrap we need these in addition:

- `datasets`
- `raw`
- `labels`

The code in `prepare` mode will create a CDF Group with the necessary capabilities
for running the `create` and `delete` modes.

### Create Mode

In order to create the desired items in CDF, the Bootstrap code must run in `create` mode. It will create the necessary
CDF Groups, Datasets and RAW Databases defined for the Aramco project.

### Delete Mode

If it is necessary to revert any changes, the `delete` mode can be used to delete CDF Groups, Datasets and RAW Databases.
Note that the CDF Groups and RAW Databases will be deleted, while Datasets will be archived and deprecated, not deleted.

## Configuration

A YAML configuration file must be passed as an argument when running the program. There are separate configuration files
for create and delete mode (prepare mode uses the same config as create mode). The configuration files file should be placed in the same directory as the program, which
is the `artifacts` folder in this example. All files in the `artifacts` folder will be pushed to Private Git In Kingdom,
available for Aramco to use. More details below.

#### Configuration for All Modes

All three modes (prepare, create and delete) require a `cognite` section and a `logger` section in the YAML config files.

Here is an example:

```yaml
# follows the same parameter structure as the DB extractor configuration
cognite: # kwargs to pass to the CogniteClient, Environment variable format: ${ENVIRONMENT_VARIABLE}
  host: ${CDF_HOST}
  project: ${CDF_PROJECT}
  # remove api_key when using ADFS authentication
  # api_key: ${COGNITE_API_KEY}
  #
  # ADFS login credentials:
  #
  idp-authentication:
    client-id: ${CDF_IDP_CLIENT_ID}
    secret: ${CDF_IDP_CLIENT_SECRET}
    scopes:
      - user_impersonation
    token_url: ${CDF_IDP_TOKEN_URL}
    resource: ${CDF_IDP_RESOURCE}


logger:
  file:
    path: .\logs\logs.log
    level: INFO
  console:
    level: INFO
```

The `cognite` section should contain all of the kwargs that should be used to instantiate the `CogniteClient`. It follows the same parameter structure as the Cognite Database Extractor.
Any secrets that are configured as environment variables should use the format: ${ENVIRONMENT_VARIABLE}.

#### Configuration for Create Mode

In addition to the sections described above, the configuration file for create mode should include three more sections:

- `environment` - used to define the working environment
- `prefix_external_id` - a flag used to enable prefixing of external IDs
- `adfs-links` - used to sync groups with AD object-ids
- `bootstrap` - used do define the facilities, use cases and cooperate application details

##### Environment

Used to define the working environment, and will be set as the prefix for naming. Example values: `dev`, `stage`, `preprod`, `prod`

```yaml
environment: preprod
```

##### Prefix External IDs

A flag used to enable prefixing of the External IDs of Datasets. Should be set to `true` **only** if there will be multiple environments (for example both `preprod` and `prod`) on a single CDF tenant. The reason is to ensure that there will be no duplicated External IDs for the CDF Datasets.

When there is only one environment per CDF tenant (which is the case for the Aramco project), we keep this flag value as `false`.

##### Adfs-links

Used to synchronize CDF Groups with AD Groups and ADFS Server-Applications. Defines the name of the CDF group, with the AD Group and ADFS Client Id as CDF group's Source ID, and a readable name as the CDF group's Source Name.

Example:

```yaml
adfs_links:
  cdf-group-name:
    - ad-group-or-adfs-client-id
    - READABLE_NAME
  preprod:root:client:
    - c222e01f-3e09-4f21-9d12-dbd7010b87c1
    - CDF_PREPROD_ROOT_CLIENT
```

##### Bootstrap

The `bootstrap` section consists of three subsections: facilities `fac`, corporate applications `ca` and use cases `uc`.

A minimal configuration file of the `bootstrap` section:

```yaml
bootstrap:
  fac:
    fac:001:name:
      description: Description text for this facility
      external_id: fac:001:name
  ca:
    ca:001:name:
      description: Description text for this corporate application
      external_id: cad:001:name
      shared_owner_access:
        - fac:001:name
  uc:
    uc:001:name:
      description: Use Case 001; Description text
      external_id: uc:001:name
      metadata:
        created: 210325
        generated: by CDF Bootstrap script
      shared_read_access:
        - fac:001:name
```

For a full example of the create configuration file, see the `config-create-preprod.yml` file in the `artifacts` folder.

#### Configuration for Delete Mode

In addition to the `config` and `logger` sections described above, the configuration file for delete mode
should include one more section:

* `delete_or_deprecate` - used to define what datasets, groups and RAW databases to be deleted (datasets are deprecated)

##### Delete_or_deprecate

This section defines what `datasets` that should be deprecated, and which `groups` and `raw_dbs` that should be deleted.

Example configuration:

```yml
delete_or_deprecate:
  datasets:
    - test:fac:001:name
  groups:
    - test:fac:001:name:owner
    - test:fac:001:name:read
  raw_dbs:
    - test:fac:001:name:rawdb
```

If nothing should be deleted, leave the subsections empty like this: `[]`.

**Tip:** After running the bootstrap in create mode, the final part of the output logs will include a "Delete template"
section. This can be used for copy-pasting in the item names you want to be added to the delete configuration file.

For a full example of the delete configuration file, see the `config-delete.yml` file in the `artifacts` folder.

# Development
Clone the repository and `cd` to the project folder.  Then, initialize the
project environment:

```sh
poetry install
```

Install the pre-commit hook:

```sh
poetry run pre-commit install
```

- the prefix `inso-` names this solution as provided by Cognite Industry Solution team, and is not (yet) an offical supported cli / GitHub Action  from Cognite
- it provides a configuration driven deployment for Cognite Bootstrap Pipelines (named `bootstrap` in short)
  - support to run it
    - from `poetry run`
    - from `python -m`
    - from `docker run`
    - and as GitHub Action

- templates used for implementation are
  - `cognitedata/transformation-cli`
  - `cognitedata/python-extratcion-utils`
    - using `CogniteConfig` and `LoggingConfig`
    - and extended with custom config sections

## to be done

- [x] `.pre-commit-config.yaml` hook support
- [x] `.dockerignore` (pycache)
- [x] logs folder handling (docker volume mount)
- [x] logger.info() or print() or click.echo(click.style(..))
    - logger debug support
- [ ] compile as EXE (when Python is not available on customer server)
  - code-signed exe required for Windows

# how to run
## run local with poetry and .env

```bash
poetry build
poetry install
poetry update

poetry run bootstrap-cli deploy --debug configs/ test-trading-bootstrap.yml
```
- Prepare mode:
```
poetry run bootstrap-cli prepare --debug configs/ test-trading-bootstrap.yml
```
- Delete mode:
```
poetry run bootstrap-cli delete --debug configs/ test-trading-bootstrap.yml
```

## run local with Python

```bash
export PYTHONPATH=.

python incubator/bootstrap_cli/__main__.py deploy configs/ test-trading-bootstrap.yml
```

## run local with Docker and .env
- `.dockerignore` file
- volumes for `configs` (to read) and `logs` folder (to write)

```bash
docker build -t incubator/bootstrap:v1.0 -t incubator/bootstrap:latest .

# ${PWD} because only absolute paths can be mounted
docker run --volume ${PWD}/configs:/configs --volume ${PWD}/logs:/logs  --env-file=.env incubator/bootstrap deploy /configs/test-trading-bootstrap.yml
```

Debug the Docker container
- requires override of `ENTRYPOINT`
- to get full functional `bash` a `Dockerfile.debug` is provided

```bash
➟  docker build -t incubator/bootstrap:debug -f Dockerfile.debug .

➟  docker run --volume ${PWD}/configs:/configs --volume ${PWD}/logs:/logs  --env-file=.env -it --entrypoint /bin/bash incubator/bootstrap:debug```

## run as github action

```yaml
jobs:
  deploy:
    name: Deploy Bootstrap Pipelines
    environment: dev
    runs-on: ubuntu-latest
    # environment variables
    env:
      CDF_PROJECT: yourcdfproject
      CDF_CLUSTER: bluefield
      IDP_TENANT: abcde-12345
      CDF_HOST: https://bluefield.cognitedata.com/
      - name: Deploy bootstrap
        uses: cognitedata/inso-expipes-cli@main
        env:
            BOOTSTRAP_IDP_CLIENT_ID: ${{ secrets.CLIENT_ID }}
            BOOTSTRAP_IDP_CLIENT_SECRET: ${{ secrets.CLIENT_SECRET }}
            BOOTSTRAP_CDF_HOST: ${{ env.CDF_HOST }}
            BOOTSTRAP_CDF_PROJECT: ${{ env.CDF_PROJECT }}
            BOOTSTRAP_IDP_TOKEN_URL: https://login.microsoftonline.com/${{ env.IDP_TENANT }}/oauth2/v2.0/token
            BOOTSTRAP_IDP_SCOPES: ${{ env.CDF_HOST }}.default
        # additional parameters for running the action
        with:
          config_file: ./configs/test-trading-bootstrap.yml
```
## End-result after Bootstrapping the CDF Tenant
### Per Facility, Corporate Application and Use Case

#### CDF Groups

For each Facility fac, Corporate Application ca and Use Case uc, there will be one owner and one read group. Following the configuration example from the section Configuration for Create Mode > Base, we generate the following CDF Groups:

- stage:fac:001:name:owner
- stage:fac:001:name:read
- stage:ca:001:name:owner
- stage:ca:001:name:read
- stage:uc:001:name:owner
- stage:uc:001:name:read

#### Raw DBs

For each Facility fac, Corporate Application ca and Use Case uc, there will be one database for data and one database for state store. Following the configuration example from the section Configuration for Create Mode > Base, we generate the following Raw DBs:

- stage:fac:001:name:rawdb
- stage:fac:001:name:rawdb:store
- stage:ca:001:name:rawdb
- stage:ca:001:name:rawdb:store
- stage:uc:001:name:rawdb
- stage:uc:001:name:rawdb:store

#### Datasets

For each Facility fac, Corporate Application ca and Use Case uc, there will be one CDF Dataset. Following the configuration example from the section Configuration for Create Mode > Base, we generate the following Datasets:

- stage:fac:001:name:dataset
- stage:ca:001:name:dataset
- stage:uc:001:name:dataset

### High-level CDF Groups, RAW DBs and Datasets

In addition to the above, we need higher-level access groups that have access to multiple entities. As an example, one facility group will only have access to the Raw DBs and Datasets for that facility. There are cases where we would need access to all facilities. Therefore, we have added additional high-level entities:

#### For all Facilities

Separate CDF Groups, RAW DBs and Datasets with aggregated access to all facilities:

Groups:

- stage:fac:allprojects:read
- stage:fac:allprojects:write

RAW DBs:

- stage:fac:allprojects:rawdb
- stage:fac:allprojects:rawdb:store

Datasets:

- stage:fac:allprojects:dataset

#### For all Corporate Applications

Separate CDF Groups, RAW DBs and Datasets with aggregated access to all corporate applications:

Groups:
- stage:ca:allprojects:read
- stage:ca:allprojects:write

RAW DBs:

- stage:ca:allprojects:rawdb
- stage:ca:allprojects:rawdb:store

Datasets:

- stage:ca:allprojects:dataset

#### For all Use Cases

Separate CDF Groups, RAW DBs and Datasets with aggregated access to all use cases:

Groups:

- stage:uc:allprojects:read
- stage:uc:allprojects:write

RAW DBs:
- stage:uc:allprojects:rawdb
- stage:uc:allprojects:rawdb:store

Datasets:

- stage:uc:allprojects:dataset

#### For all Three

Separate CDF Groups, RAW DBs and Datasets with aggregated access to all facilities, corporate applications and use cases:

Groups:

- stage:allprojects:read
- stage:allprojects:write

RAW DBs:

- stage:allprojects:rawdb
- stage:allprojects:rawdb:store

Datasets:

- stage:allprojects:dataset

#### Root User

In addition, we need to have a user that is not limited to the facilities, corporate applications and use cases. Therefore, we have a root user. It does not require separate RAW DBs and Datasets, so there are only two groups created for this:

- stage:root:client
- stage:root:user

(Note: the client has the capabilities corresponding to an owner group, and the user has the capabilities corresponding to a read group).
