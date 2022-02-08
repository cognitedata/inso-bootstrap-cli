# CDF Project Bootstrap

Configuration driven bootstrap of CDF Groups, Datasets, RAW Databases with data separation on
sources, use-case and user-input level. Allowing (configurable) shared-access between each other for the solutions (like server-applications) running transformations or use-cases.

## Table of Content
<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

<!-- code_chunk_output -->

- [Inso-Bootstrap-cli](#inso-bootstrap-cli)
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

### Prerequisites (Prepare command)

The first time you want to run boostrap-cli for your new CDF project, the `prepare` command might be required.

- A new CDF Project is only configured with one CDF Group (named like "OIDC admin") which covers these capabilities:
  - `projects`
  - `groups`

To run bootstrap-cli additional capabilties are required:

- `datasets`
- `raw`

The `prepare` command will provide you with another CDF Group `cdf:bootstrap` with this minimal capabilities.

### Deploy command

The bootstrap-cli `deploy` command will apply the configuration-file to your CDF Project. 
It will create the necessary CDF Groups, Datasets and RAW Databases.
This command supports GitHub-Action workflow too.

### Delete command

If it is necessary to revert any changes, the `delete` mode can be used to delete CDF Groups, Datasets and RAW Databases.
Note that the CDF Groups and RAW Databases will be deleted, while Datasets will be archived and deprecated, not deleted.

## Configuration

A YAML configuration file must be passed as an argument when running the program. There are separate configuration files
for create and delete mode (prepare mode uses the same config as create mode). The configuration files file should be placed in the same directory as the program, which
is the `artifacts` folder in this example. All files in the `artifacts` folder will be pushed to Private Git In Kingdom,
available for Aramco to use. More details below.

#### Configuration for all commands

All commands require share a `cognite` section and a `logger` section in the YAML config files, which is common to our Cognite Database-Extractor configuration.
The configuration file supports variable-expansion (`${BOOTSTRAP_**}`), which are provided either as 
1. environment-variables, 
2. from a `.env` file or 
3. command-line parameters

Here is an example:

```yaml
# follows the same parameter structure as the DB extractor configuration
cognite:
  host: ${BOOTSTRAP_CDF_HOST}
  project: ${BOOTSTRAP_CDF_PROJECT}
  #
  # AAD IdP login:
  #
  idp-authentication:
    client-id: ${BOOTSTRAP_IDP_CLIENT_ID}
    secret: ${BOOTSTRAP_IDP_CLIENT_SECRET}
    scopes:
      - ${BOOTSTRAP_IDP_SCOPES}
    token_url: ${BOOTSTRAP_IDP_TOKEN_URL}

logger:
  file:
    path: ./logs/test-deploy.log
    level: INFO
  console:
    level: INFO
```

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


##### AAD Group to CDF Group mapping

Used to link CDF Groups with AAD Groups. 
Defines the name of the CDF Group, with the AAD Group object-id, and for documentation the AAD Group name.

Example:

```yaml
aad_mappings:
  #cdf-group-name:
  #  - aad-group-object-id
  #  - READABLE_NAME
  cdf:allprojects:owner:
    - 123456-7890-abcd-1234-314159
    - CDF_DEV_ALLPROJECTS_OWNER
```

TODO
##### Bootstrap (TO BE DONE)

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

* `delete_or_deprecate` - used to define which CDF Datasets, CDF Groups and RAW databases (including tables) should to be deleted (CDF Datasets are in-fact only deprecated, as they cannot be deleted)

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

**Tip:** After running the bootstrap in `deploy` mode, the final part of the output logs will include a "Delete template"
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
