# Inso Bootstrap Cli

Configuration driven bootstrap of CDF Groups, Datasets, RAW Databases with data separation on
sources, use-case and user-input level. Allowing (configurable) shared-access between each other for the solutions (like server-applications) running transformations or use-cases.

## Table of Content
<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

<!-- code_chunk_output -->

- [Inso Bootstrap Cli](#inso-bootstrap-cli)
  - [Table of Content](#table-of-content)
  - [Bootstrap Run Modes](#bootstrap-run-modes)
    - [Prerequisites (Prepare command)](#prerequisites-prepare-command)
    - [Deploy command](#deploy-command)
    - [Delete command](#delete-command)
  - [Configuration](#configuration)
    - [Configuration for all commands](#configuration-for-all-commands)
      - [Configuration for deploy command](#configuration-for-deploy-command)
      - [`aad_mappings` section: AAD Group to CDF Group mapping](#aad_mappings-section-aad-group-to-cdf-group-mapping)
        - [`bootstrap` section](#bootstrap-section)
      - [Configuration for delete command](#configuration-for-delete-command)
        - [`delete_or_deprecate` section](#delete_or_deprecate-section)
- [Development](#development)
  - [to be done](#to-be-done)
- [how to run](#how-to-run)
  - [run local with poetry](#run-local-with-poetry)
  - [run local with Python](#run-local-with-python)
  - [run local with Docker](#run-local-with-docker)
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

A YAML configuration file must be passed as an argument when running the program.
Different configuration file used for delete and prepare/deploy

### Configuration for all commands

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

#### Configuration for deploy command

In addition to the sections described above, the configuration file for deploy mode should include two more sections:

- `aad_mappings` - used to sync CDF Groups with AAD Group object-ids
- `bootstrap` - used do define the logical access-control groups

#### `aad_mappings` section: AAD Group to CDF Group mapping

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

##### `bootstrap` section

The `bootstrap` section allows a two-level configuration of access-control groups:

Like for example:

- `src` for sources,
- `ca` for corporate applications,
- `in` for user-input control,
- and typically `uc` for use cases (which represent the solution and is  built on top of the others)

A minimal configuration file of the `bootstrap` section:

```yaml
bootstrap:
  src:
    src:001:name:
      description: Description about sources related to name
      external_id: src:001:name
  in:
    in:001:name:
      description: Description about user inputs related to name
      external_id: in:001:name
  uc:
    uc:001:name:
      description: Description about use case
      external_id: uc:001:name
      metadata:
        created: 210325
        generated: by cdf-config-hub script
      shared_read_access:
        - src:001:name
      shared_owner_access:
        - in:001:name
```

For a full example of the deploy(create) configuration file, see the `configs/test-bootstrap-deploy-example.yml` file.

#### Configuration for delete command

In addition to the `config` and `logger` sections described above, the configuration file for delete mode
should include one more section:

* `delete_or_deprecate` - used to define which CDF Datasets, CDF Groups and RAW databases (including tables) should to be deleted (CDF Datasets are in-fact only deprecated, as they cannot be deleted)

##### `delete_or_deprecate` section

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

For a full example of the delete configuration file, see the `configs/test-bootstrap-delete-example.yaml` file.

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

Follow the initial setup first
1. Fill out relevant configurations from `configs`
1.1. Fill out `aad_mappings` and `bootstrap` from `test-bootstrap-deploy-example.yml`
1.2. Fill out `delete_or_deprecate` from test-bootstrap-delete-example.yml
2. Change `.env_example` to `.env`
3. Fill out `.env`
## run local with poetry

```bash
  poetry build
  poetry install
  poetry update
```
- Deploy mode:
```
  poetry run bootstrap-cli deploy --debug configs/ test-bootstrap-deploy-example.yml
```
- Prepare mode:
```
  poetry run bootstrap-cli prepare --debug configs/ test-bootstrap-deploy-example.yml
```
- Delete mode:
```
  poetry run bootstrap-cli delete --debug configs/ test-bootstrap-delete-example.yml
```

## run local with Python

```bash
export PYTHONPATH=.

python incubator/bootstrap_cli/__main__.py deploy configs/ test-bootstrap-deploy-example.yml
```

## run local with Docker
- `.dockerignore` file
- volumes for `configs` (to read) and `logs` folder (to write)

```bash
docker build -t incubator/bootstrap:v1.0 -t incubator/bootstrap:latest .

# ${PWD} because only absolute paths can be mounted
docker run --volume ${PWD}/configs:/configs --volume ${PWD}/logs:/logs  --env-file=.env incubator/bootstrap deploy /configs/test-bootstrap-deploy-example.yml
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
          config_file: ./configs/test-bootstrap-deploy-example.yml
```
