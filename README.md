# InSo Bootstrap CLI

## Scope of Work

Disclaimer:
> The repository name is prefixed with `inso-`, marking this solution as provided by Cognite Industry Solution (InSo) team, but is not an offical supported CLI / GitHub Action from Cognite with product-grade SLOs.

Purpose:

- Providing a configuration driven bootstrap of CDF Groups, Datasets, RAW Databases with data-separation on sources, use-case and user-input level.
- Aiming for **DAY1**:
  - the initial-setup phase: your first configuration of a new CDF Project
- Support for **DAY2**:
  - the operational phase: running maintenance and change-management against your scaled (multiple) CDF Projects


## Table of Content
<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

<!-- code_chunk_output -->

- [InSo Bootstrap CLI](#inso-bootstrap-cli)
  - [Scope of Work](#scope-of-work)
  - [Table of Content](#table-of-content)
  - [How to get started](#how-to-get-started)
  - [Bootstrap CLI concept](#bootstrap-cli-concept)
    - [Secure access management](#secure-access-management)
    - [Data Sets](#data-sets)
  - [Bootstrap CLI makes Access-Control and Data Lineage manageable](#bootstrap-cli-makes-access-control-and-data-lineage-manageable)
    - [Namespaces](#namespaces)
    - [Templating](#templating)
    - [Packaging](#packaging)
    - [Bootstrap CLI example](#bootstrap-cli-example)
      - [Groups](#groups)
      - [Scopes](#scopes)
  - [Bootstrap CLI commands](#bootstrap-cli-commands)
    - [`Prepare` command](#prepare-command)
    - [`Deploy` command](#deploy-command)
    - [`Delete` command](#delete-command)
    - [`Diagram` command](#diagram-command)
  - [Configuration](#configuration)
    - [Configuration for all commands](#configuration-for-all-commands)
      - [Configuration for `deploy` command](#configuration-for-deploy-command)
      - [`aad_mappings` section: AAD Group to CDF Group mapping](#aad_mappings-section-aad-group-to-cdf-group-mapping)
        - [`bootstrap` section](#bootstrap-section)
      - [Configuration for `delete` command](#configuration-for-delete-command)
        - [`delete_or_deprecate` section](#delete_or_deprecate-section)
- [Development / Contribute](#development--contribute)
  - [semantic versioning](#semantic-versioning)
  - [to be done](#to-be-done)
- [how to run](#how-to-run)
  - [run local with poetry](#run-local-with-poetry)
  - [run local with Python](#run-local-with-python)
  - [run local with Docker](#run-local-with-docker)
  - [run as github action](#run-as-github-action)


## How to get started

The recommended way to run this is using poetry, but other methods are supported.
For more details on other methods or native windows usage, check out [How to run](#how-to-run).
To start you have to install Poetry, a tool to manage python dependencies and virtual environments. It is recommended running this on Linux, WSL2 or Mac. 

```
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
```

Once poetry has been install, the local python environment can be installed and set up using poetry.

```
poetry build
poetry install
poetry update
```


### Minimal Configuration
Before running the cli, you have to set up your config file. A goo start is to take a look at the following config file. 

- `config/config-simple-v2-draft.yml` 

This config has extensive comments explaining the syntax with examples for all the important features. More explanation can also be found in the [Configuration](#configuration)-section

This tool has four main commands:

- `diagram`
  - Diagram mode used to document the given configuration as a mermaid diagram
- `prepare`
  - Prepare an elevated CDF Group 'cdf:bootstrap' and link it to an idp-group
- `deploy `
  - Deploy a set of bootstrap from a config-file
- `delete` 
  - Delete mode used to delete CDF Groups, Datasets and Raw Databases

To test the tool out without connecting to a CDF-project, comment out the cognite-section of the config an run the `diagram` command (on WSL):

```
 poetry run bootstrap-cli --debug diagram --cdf-project=shiny-dev configs/config-simple-v2-draft.yml | clip.exe
``` 

alternativly on Mac/Linux

```
 poetry run bootstrap-cli --debug diagram --cdf-project=shiny-dev configs/config-simple-v2-draft.yml > diagram.txt
``` 

No you can go to [Mermaid Live](https://mermaid.live/) and paste the content of the clipboard/file and see a diagram of the Groups, Data Sets and Raw-DBs the tool would create based on this config file.

#### Authentication 

The easies way to set up authentication is to copy the `.env_example` file to `.env` and fill out the environment variables needed. For informations on the fields see  the [Environment variables](#environment-variables)-section.

Once the `.env` file is set up, you can check that the tool can connect to CDF by uncommenting the cognite-part of the config file and re-running the `diagram` command from above. 


### Running locally

With To set create a group with the proper access-rights for the bootstrap-cli to do it's job you can run the `prepare`-command. this creates a group and links it to a group the app-registration is in. 

PS. It is possible to run all of commands in dry-run mode by specifying `--dry-run=yes` before the command. This wil log the intended API-actions.

```
poetry run bootstrap-cli --debug prepare --aad-source-id <idb-source-id>
```
For more information, see the [Prepare command](#prepare-command)-section.

Once the prepare command has been run, the cli should have the rights it needs and you are ready to run the deploy command. 

```
poetry run bootstrap-cli --debug deploy --cdf-project=shiny-dev configs/config-simple-v2-draft.yml
```

This will deploy and create all the groups, data sets and raw dbs shown in the diagram created above. 
If they alreay exist, the tool will update/recreate them based on the config file. 

### Github Action

To run this on GitHub-Actions here is an example workflow for deploying using github actions:

```yaml
jobs:
  deploy:
    name: Deploy Bootstrap Pipelines
    environment: dev
    runs-on: ubuntu-latest
    # environment variables
    env:
      CDF_PROJECT: yourcdfproject
      CDF_CLUSTER: yourcdfcluster
      IDP_TENANT: your-idf-cliend-id
      CDF_HOST: https://yourcdfcluster.cognitedata.com/
      # use a tagged release like @v2.0.0
      # - uses: cognitedata/inso-bootstrap-cli@v2.0.0
      # or use the latest release available using @main
      - uses: cognitedata/inso-bootstrap-cli@main
        env:
            BOOTSTRAP_IDP_CLIENT_ID: ${{ secrets.CLIENT_ID }}
            BOOTSTRAP_IDP_CLIENT_SECRET: ${{ secrets.CLIENT_SECRET }}
            BOOTSTRAP_CDF_HOST: ${{ env.CDF_HOST }}
            BOOTSTRAP_CDF_PROJECT: ${{ env.CDF_PROJECT }}
            BOOTSTRAP_IDP_TOKEN_URL: https://login.microsoftonline.com/${{ env.IDP_TENANT }}/oauth2/v2.0/token
            BOOTSTRAP_IDP_SCOPES: ${{ env.CDF_HOST }}.default
        # additional parameters for running the action
        with:
          config_file: ./configs/config-simple-v2-draft.yml
          # "yes"|"no" deploy with special groups and aad_mappings
          with_special_groups: "yes"
```



<!-- /code_chunk_output -->
## Bootstrap CLI concept

The Bootstrap CLI aims to tackle both DAY1 and DAY2 activities releated to Access Management. This include:
- Groups
- Scopes
  - Data Sets
  - RAW DBs


**DAY1** activities are initial setup and configurations before a system can be used.
Followed by **DAY2** activities which are the operational use of the system and scaling.

Cognite provides support for a list of **DAY1** activities, to enable governance best-practices from the start, such as:

* **Secure access management** to control access for users, apps and services to the various types of resources (data sets, assets, files, events, time series, etc.) in CDF
* **Data Sets** to document and track data lineage
* **Data quality** like monitoring the data integration pipelines into CDF

As all of this is connected to each other, and it is spanning customers Identity Provider (Azure AD) and CDF, this tool utilizes the CDF API for a configuration driven approach for the CDF part.

### Secure access management

**Secure access management** requires connection of Azure AD (AAD) Groups to CDF Groups. User or app Authentication is provided by customers AAD and Authorization by CDF Groups. CDF Groups are defined through capabilities and actions (like "Timeseries" capability with "Read/Write" actions).

**Secure access management** related configuration targets:
* CDF Groups and links to AAD Groups
* AAD-owner responsibilities:
  * AAD Group creation
  * Service-principal (user and apps) creation and mapping to AAD Groups

### Data Sets

CDF **Data Sets** are used to scope CDF Groups capabilties to a set of CDF Resources. This allows fencing future usage, to stay within this scope. Creation of new Data Sets is a governace related action, and is executed by a defined process. An exception is CDF RAW data which is scoped through CDF RAW Databases.

CDF **Scopes** related configuration targets:
* CDF Data Sets
* CDF RAW Databases

## Bootstrap CLI makes Access-Control and Data Lineage manageable

CDF Groups allows creation of very complex configurations the many different capabilities (~30), actions (2-5) and scopes (x). To establish a **manageable** and **understandable** access-control & data-lineage, the `bootstrap-cli` uses an approach to reduce the complexity by templating and packaging. In addition namespaces help add operational semantic (meaning).

### Namespaces

A two-layered hierarchy allows organization of a growing list of CDF Groups.

The first layer of the hierarchy is a namespace and the second one is individual elements within a namespace. An example of this could be having the following namespaces with explanation for why this could be a good idea:

- **src**: to scope 3rd party sources
- **fac**: to scope customer facilities by name
- **ca**: to scope "corporate applications" (SAP, Salesforce, ..)
- **uc**: to scope your use-cases ("UC:001 - Flow Optimization", "UC:002 - Trading Balances"
- **in**: to scope user-input from UIs

A namespace allows each project to apply **the** operational semantic, which fits your project and customers terminology.

This is just an example of namespaces used in projects today, but you are free to chose whatever names fit your project.

Good style is to keep the names short and add long names and details to the `description` fields.

### Templating

1. CDF Groups are created in `OWNER` and `READ` pairs
   - **All** capabilities are handled the same, and are applied
     - as either an `OWNWER`-set
     - or as a `READ`-only-set
   - access-control only works through scopes, but within your scopes you can work w/o limits
2. The CDF Groups can be called "strict-scoped" meaning that access-control to this group only allows reading and writing data to the available scopes
   - no data can exist outside the predefined scopes
   - no user or app can create additional scopes

### Packaging

1. Every `OWNER/READ` pair of CDF Groups is configured with the same package of scopes:
   - two RAW DBs (one for staging, one for state-stores)
   - one Data Set (for all CDF Resource types, as capabilities are not restricted)
   -  `OWNER` Groups can be configured with additional shared-access to scopes of other CDF Groups
   - this allows users (or apps) working on a Use-Case (`uc`)
     1. to read data from scopes of other Source (`src`) groups and
     2. to write the processed and value-added data to its own scope
     3. allowing data-lineage from sources through use-case model to data-products

### Bootstrap CLI example
Here is an extract from the example config `config-simple-v2-draft.yml` wich uses the main abilities of the CLI. 

```yaml
bootstrap:
  features:
    aggregated-level-name: all
    dataset-suffix: ds
    rawdb-suffix: db
  idp-cdf-mappings:
    - cdf-project: shiny-dev
      - cdf-group: cdf:all:owner
          idp-source-id: acd2fe35-aa51-45a7-acef-11111111111
          idp-source-name: CDF_DEV_ALLPROJECTS_OWNER
      - cdf-group: .....
        ...    
  namespaces:
    - ns-name: src
      description: Customer source-systems
      ns-nodes:
        - node-name: src:001:sap
          description: Sources 001; from SAP
          external-id: src:001:sap
        - node-name: src:002:weather
          description: Sources 002; from Weather.com
          # external-id will be auto generated in this case

    - ns-name: in 
      description: End user data-input provided through deployed CDF driven solutions
      ns-nodes:
        - node-name: in:001:trade
          description: Description about user inputs related to name
          # external_id: in:001:trade

    - ns-name: uc
      description: Use Cases representing the data-products
      ns-nodes:
        - node-name: uc:001:demand
          description: Use Case 001; Supply and Demand
          metadata:
            created: 220427
            generated: by cdf-config-hub script
          shared-access:
            read:
              - node-name: src:001:sap
              - node-name: src:002:weather
            owner:
              - node-name: in:001:trade
```

Using the diagram functionalty of the CLI we can produce the following chart of the example config `config-simple-v2-draft.yml`. The stipulated lines show read-access and the solid ones write.

```mermaid
graph LR
%% 2022-05-16 14:08:18 - Script generated Mermaid diagram

subgraph "idp" ["IdP Groups for CDF: 'shiny-dev'"]
  %% IdP objectId: 314159-aa51-45a7-acef-11111111111
CDF_DEV_UC001DEMAND_READ[\"CDF_DEV_UC001DEMAND_READ"/]
  %% IdP objectId: acd2fe35-aa51-45a7-acef-11111111111
CDF_DEV_all_READ[\"CDF_DEV_all_READ"/]
  %% IdP objectId: acd2fe35-aa51-45a7-acef-11111111111
CDF_DEV_all_OWNER[\"CDF_DEV_all_OWNER"/]
end


subgraph "owner" ["'Owner' Groups"]
  
subgraph "core_cdf_owner" ["Node Level (Owner)"]
  cdf:src:001:sap:owner("cdf:src:001:sap:owner")
  cdf:src:002:weather:owner("cdf:src:002:weather:owner")
  cdf:in:001:trade:owner("cdf:in:001:trade:owner")
  cdf:uc:001:demand:owner("cdf:uc:001:demand:owner")
end

  
subgraph "ns_cdf_owner" ["Namespace Level (Owner)"]
  cdf:src:all:owner["cdf:src:all:owner"]
  cdf:in:all:owner["cdf:in:all:owner"]
  cdf:uc:all:owner["cdf:uc:all:owner"]
  cdf:all:owner["cdf:all:owner"]
end

  
subgraph "scope_owner" ["Scopes (Owner)"]
  src:001:sap:db__owner__raw[["src:001:sap:db"]]
  src:001:sap:db:state__owner__raw[["src:001:sap:db:state"]]
  src:001:sap:ds__owner__datasets>"src:001:sap:ds"]
  src:002:weather:db__owner__raw[["src:002:weather:db"]]
  src:002:weather:db:state__owner__raw[["src:002:weather:db:state"]]
  src:002:weather:ds__owner__datasets>"src:002:weather:ds"]
  src:all:db__owner__raw[["src:all:db"]]
  src:all:db:state__owner__raw[["src:all:db:state"]]
  src:all:ds__owner__datasets>"src:all:ds"]
  in:001:trade:db__owner__raw[["in:001:trade:db"]]
  in:001:trade:db:state__owner__raw[["in:001:trade:db:state"]]
  in:001:trade:ds__owner__datasets>"in:001:trade:ds"]
  in:all:db__owner__raw[["in:all:db"]]
  in:all:db:state__owner__raw[["in:all:db:state"]]
  in:all:ds__owner__datasets>"in:all:ds"]
  uc:001:demand:db__owner__raw[["uc:001:demand:db"]]
  uc:001:demand:db:state__owner__raw[["uc:001:demand:db:state"]]
  in:001:trade:db__owner__raw[["in:001:trade:db"]]
  in:001:trade:db:state__owner__raw[["in:001:trade:db:state"]]
  uc:001:demand:ds__owner__datasets>"uc:001:demand:ds"]
  in:001:trade:ds__owner__datasets>"in:001:trade:ds"]
  src:001:sap:db__owner__raw[["src:001:sap:db"]]
  src:001:sap:db:state__owner__raw[["src:001:sap:db:state"]]
  src:002:weather:db__owner__raw[["src:002:weather:db"]]
  src:002:weather:db:state__owner__raw[["src:002:weather:db:state"]]
  src:001:sap:ds__owner__datasets>"src:001:sap:ds"]
  src:002:weather:ds__owner__datasets>"src:002:weather:ds"]
  uc:all:db__owner__raw[["uc:all:db"]]
  uc:all:db:state__owner__raw[["uc:all:db:state"]]
  uc:all:ds__owner__datasets>"uc:all:ds"]
  all:db__owner__raw[["all:db"]]
  all:db:state__owner__raw[["all:db:state"]]
  all:ds__owner__datasets>"all:ds"]
end

end


subgraph "read" ["'Read' Groups"]
  
subgraph "core_cdf_read" ["Node Level (Read)"]
  cdf:src:001:sap:read("cdf:src:001:sap:read")
  cdf:src:002:weather:read("cdf:src:002:weather:read")
  cdf:in:001:trade:read("cdf:in:001:trade:read")
  cdf:uc:001:demand:read("cdf:uc:001:demand:read")
end

  
subgraph "ns_cdf_read" ["Namespace Level (Read)"]
  cdf:src:all:read["cdf:src:all:read"]
  cdf:in:all:read["cdf:in:all:read"]
  cdf:uc:all:read["cdf:uc:all:read"]
  cdf:all:read["cdf:all:read"]
end

  
subgraph "scope_read" ["Scopes (Read)"]
  src:001:sap:db__read__raw[["src:001:sap:db"]]
  src:001:sap:db:state__read__raw[["src:001:sap:db:state"]]
  src:001:sap:ds__read__datasets>"src:001:sap:ds"]
  src:002:weather:db__read__raw[["src:002:weather:db"]]
  src:002:weather:db:state__read__raw[["src:002:weather:db:state"]]
  src:002:weather:ds__read__datasets>"src:002:weather:ds"]
  src:all:db__read__raw[["src:all:db"]]
  src:all:db:state__read__raw[["src:all:db:state"]]
  src:all:ds__read__datasets>"src:all:ds"]
  in:001:trade:db__read__raw[["in:001:trade:db"]]
  in:001:trade:db:state__read__raw[["in:001:trade:db:state"]]
  in:001:trade:ds__read__datasets>"in:001:trade:ds"]
  in:all:db__read__raw[["in:all:db"]]
  in:all:db:state__read__raw[["in:all:db:state"]]
  in:all:ds__read__datasets>"in:all:ds"]
  uc:001:demand:db__read__raw[["uc:001:demand:db"]]
  uc:001:demand:db:state__read__raw[["uc:001:demand:db:state"]]
  uc:001:demand:ds__read__datasets>"uc:001:demand:ds"]
  uc:all:db__read__raw[["uc:all:db"]]
  uc:all:db:state__read__raw[["uc:all:db:state"]]
  uc:all:ds__read__datasets>"uc:all:ds"]
  all:db__read__raw[["all:db"]]
  all:db:state__read__raw[["all:db:state"]]
  all:ds__read__datasets>"all:ds"]
end

end

%% all 74 links connecting the above nodes
cdf:src:all:read-.->cdf:src:001:sap:read
cdf:src:001:sap:read-.->src:001:sap:db__read__raw
cdf:src:001:sap:read-.->src:001:sap:db:state__read__raw
cdf:src:001:sap:read-.->src:001:sap:ds__read__datasets
cdf:src:all:read-.->cdf:src:002:weather:read
cdf:src:002:weather:read-.->src:002:weather:db__read__raw
cdf:src:002:weather:read-.->src:002:weather:db:state__read__raw
cdf:src:002:weather:read-.->src:002:weather:ds__read__datasets
cdf:all:read-.->cdf:src:all:read
cdf:src:all:read-.->src:all:db__read__raw
cdf:src:all:read-.->src:all:db:state__read__raw
cdf:src:all:read-.->src:all:ds__read__datasets
cdf:in:all:read-.->cdf:in:001:trade:read
cdf:in:001:trade:read-.->in:001:trade:db__read__raw
cdf:in:001:trade:read-.->in:001:trade:db:state__read__raw
cdf:in:001:trade:read-.->in:001:trade:ds__read__datasets
cdf:all:read-.->cdf:in:all:read
cdf:in:all:read-.->in:all:db__read__raw
cdf:in:all:read-.->in:all:db:state__read__raw
cdf:in:all:read-.->in:all:ds__read__datasets
CDF_DEV_UC001DEMAND_READ-->cdf:uc:001:demand:read
cdf:uc:all:read-.->cdf:uc:001:demand:read
cdf:uc:001:demand:read-.->uc:001:demand:db__read__raw
cdf:uc:001:demand:read-.->uc:001:demand:db:state__read__raw
cdf:uc:001:demand:read-.->uc:001:demand:ds__read__datasets
cdf:all:read-.->cdf:uc:all:read
cdf:uc:all:read-.->uc:all:db__read__raw
cdf:uc:all:read-.->uc:all:db:state__read__raw
cdf:uc:all:read-.->uc:all:ds__read__datasets
CDF_DEV_all_READ-->cdf:all:read
cdf:all:read-.->all:db__read__raw
cdf:all:read-.->all:db:state__read__raw
cdf:all:read-.->all:ds__read__datasets
cdf:src:all:owner-->cdf:src:001:sap:owner
cdf:src:001:sap:owner-->src:001:sap:db__owner__raw
cdf:src:001:sap:owner-->src:001:sap:db:state__owner__raw
cdf:src:001:sap:owner-->src:001:sap:ds__owner__datasets
cdf:src:all:owner-->cdf:src:002:weather:owner
cdf:src:002:weather:owner-->src:002:weather:db__owner__raw
cdf:src:002:weather:owner-->src:002:weather:db:state__owner__raw
cdf:src:002:weather:owner-->src:002:weather:ds__owner__datasets
cdf:all:owner-->cdf:src:all:owner
cdf:src:all:owner-->src:all:db__owner__raw
cdf:src:all:owner-->src:all:db:state__owner__raw
cdf:src:all:owner-->src:all:ds__owner__datasets
cdf:in:all:owner-->cdf:in:001:trade:owner
cdf:in:001:trade:owner-->in:001:trade:db__owner__raw
cdf:in:001:trade:owner-->in:001:trade:db:state__owner__raw
cdf:in:001:trade:owner-->in:001:trade:ds__owner__datasets
cdf:all:owner-->cdf:in:all:owner
cdf:in:all:owner-->in:all:db__owner__raw
cdf:in:all:owner-->in:all:db:state__owner__raw
cdf:in:all:owner-->in:all:ds__owner__datasets
cdf:uc:all:owner-->cdf:uc:001:demand:owner
cdf:uc:001:demand:owner-->uc:001:demand:db__owner__raw
cdf:uc:001:demand:owner-->uc:001:demand:db:state__owner__raw
cdf:uc:001:demand:owner-->in:001:trade:db__owner__raw
cdf:uc:001:demand:owner-->in:001:trade:db:state__owner__raw
cdf:uc:001:demand:owner-->uc:001:demand:ds__owner__datasets
cdf:uc:001:demand:owner-->in:001:trade:ds__owner__datasets
cdf:uc:001:demand:owner-.->src:001:sap:db__owner__raw
cdf:uc:001:demand:owner-.->src:001:sap:db:state__owner__raw
cdf:uc:001:demand:owner-.->src:002:weather:db__owner__raw
cdf:uc:001:demand:owner-.->src:002:weather:db:state__owner__raw
cdf:uc:001:demand:owner-.->src:001:sap:ds__owner__datasets
cdf:uc:001:demand:owner-.->src:002:weather:ds__owner__datasets
cdf:all:owner-->cdf:uc:all:owner
cdf:uc:all:owner-->uc:all:db__owner__raw
cdf:uc:all:owner-->uc:all:db:state__owner__raw
cdf:uc:all:owner-->uc:all:ds__owner__datasets
CDF_DEV_all_OWNER-->cdf:all:owner
cdf:all:owner-->all:db__owner__raw
cdf:all:owner-->all:db:state__owner__raw
cdf:all:owner-->all:ds__owner__datasets
```

As one can see, even for this simple use case, the cli creates quite a lot of resources. The reason for this is to both provide the outward simplicity of a DAY1 setup like it is shown here, but with the possibility to add more granular group control later on. In this DAY1 setup, only the two top groups and one use-case group are mapped to actual AAD-groups.

If we take a closer look at only the first namespace node.
```
src:001:sap
```
For this element the cli creates/updates the following resources:
#### Groups
```
cdf:all:owner
cdf:all:read

cdf:src:all:owner
cdf:src:all:read

cdf:src:001:sap:owner
cdf:src:001:sap:read
```
#### Scopes
```
all:dataset
all:db
all:db:state

src:all:ds
src:all:db
src:all:db:state

src:001:sap:ds
src:001:sap:db
src:001:sap:db:state
```

This allows us to give access to for example all sources or just to a specific one like src:001 while forcing data to always be written into datasets.


## Bootstrap CLI commands

Common parameters for all commands, which most are typically provided through environment variables (prefixed with `BOOTSTRAP_`):

```text
Usage: bootstrap-cli [OPTIONS] COMMAND [ARGS]...

Options:
  --version                Show the version and exit.
  --cdf-project-name TEXT  CDF Project to interact with CDF API,
                           'BOOTSTRAP_CDF_PROJECT',environment variable can be
                           used instead. Required for OAuth2 and optional for
                           api-keys.
  --cluster TEXT           The CDF cluster where CDF Project is hosted (e.g.
                           greenfield, europe-west1-1),Provide this or make
                           sure to set 'BOOTSTRAP_CDF_CLUSTER' environment
                           variable. Default: westeurope-1
  --host TEXT              The CDF host where CDF Project is hosted (e.g.
                           https://bluefield.cognitedata.com),Provide this or
                           make sure to set 'BOOTSTRAP_CDF_HOST' environment
                           variable.Default:
                           https://bluefield.cognitedata.com/
  --api-key TEXT           API key to interact with CDF API. Provide this or
                           make sure to set
                           'BOOTSTRAP_CDF_API_KEY',environment variable if you
                           want to authenticate with API keys.
  --client-id TEXT         IdP Client ID to interact with CDF API. Provide
                           this or make sure to set,'BOOTSTRAP_IDP_CLIENT_ID'
                           environment variable if you want to authenticate
                           with OAuth2.
  --client-secret TEXT     IdP Client secret to interact with CDF API. Provide
                           this or make sure to
                           set,'BOOTSTRAP_IDP_CLIENT_SECRET' environment
                           variable if you want to authenticate with OAuth2.
  --token-url TEXT         IdP Token URL to interact with CDF API. Provide
                           this or make sure to set,'BOOTSTRAP_IDP_TOKEN_URL'
                           environment variable if you want to authenticate
                           with OAuth2.
  --scopes TEXT            IdP Scopes to interact with CDF API, relevant for
                           OAuth2 authentication method,'BOOTSTRAP_IDP_SCOPES'
                           environment variable can be used instead.
  --audience TEXT          IdP Audience to interact with CDF API, relevant for
                           OAuth2 authentication
                           method,'BOOTSTRAP_IDP_AUDIENCE' environment
                           variable can be used instead.
  --dotenv-path TEXT       Provide a relative or absolute path to an .env file
                           (for commandline usage only)
  --debug                  Print debug information
  --dry-run [yes|no]       Only logging planned CDF API action while doing
                           nothing. Defaults to 'no'
  -h, --help               Show this message and exit.

Commands:
  delete   Delete mode used to delete CDF Groups, Datasets and Raw...
  deploy   Deploy a set of bootstrap from a config-file
  diagram  Diagram mode used to document the given configuration as a...
  prepare  Prepare an elevated CDF Group 'cdf:bootstrap', using the same...
```
### `Prepare` command

The first time you plan to run `bootstrap-cli` for your new CDF project, the `prepare` is required to create a CDF Group with capabilities which allows it to run the other commands.

A new CDF Project is typically only configured with one CDF Group (named `oidc-admin-group`) which grants these capabilities:
  - `projects:[read,list,update]`
  - `groups:[create,delete,update,list,read]`

To run bootstrap-cli additional capabilities (and actions) are required:

- `datasets:[read,write,owner]`
- `raw:[read,write,list]`

The `prepare` command creates a new CDF Group named `cdf:bootstrap` with this capabilities.
The command requires an AAD Group ID to link to, which typically for a new project is the one configured
for the CDF Group named `oidc-admin-group`. How to aquire it:

1. Login to Fusion
2. Navigate to Manage Access
3. filter for `oidc-admin-group`
4. Edit and copy the value from "Source ID"
5. provide it as `--aad-source-id=<source-id>` parameter to the `prepare` command and your configuration file

```text
Usage: bootstrap-cli prepare [OPTIONS] [CONFIG_FILE]

  Prepare an elevated CDF Group 'cdf:bootstrap', using the same AAD Group link
  as your initially provided 'oidc-admin-group'. With additional capabilities
  to to run the 'deploy' and 'delete' commands next. The 'prepare' command is
  only required once per CDF Project.

Options:
  --aad-source-id TEXT  [required] Provide the AAD Source ID to use for the
                        'cdf:bootstrap' Group. Typically for a new project its
                        the one configured for the CDF Group named 'oidc-
                        admin-group'.  [required]
  -h, --help            Show this message and exit.
```

### `Deploy` command

The bootstrap-cli `deploy` command will apply the configuration-file to your CDF Project.
It will create the necessary CDF Groups, Datasets and RAW Databases.
This command supports GitHub-Action workflow too. To check what this command is going to do, run it with the flag `--dry-run=yes`.

```text
Usage: bootstrap-cli deploy [OPTIONS] [CONFIG_FILE]

  Deploy a set of bootstrap from a config-file

Options:
  --with-special-groups [yes|no]  Create special CDF Groups, which don't have
                                  capabilities (extractions, transformations).
                                  Defaults to 'no'
  --with-raw-capability [yes|no]  Create RAW DBs and 'rawAcl' capability.
                                  Defaults to 'yes'
  -h, --help                      Show this message and exit.
```

### `Delete` command

If it is necessary to revert any changes, the `delete` mode can be used to delete CDF Groups, Datasets and RAW Databases.
Note that the CDF Groups and RAW Databases will be deleted, while Datasets will be archived and deprecated, not deleted. To check what this command is going to do, run it with the flag `--dry-run=yes`.

```text
Usage: bootstrap-cli delete [OPTIONS] [CONFIG_FILE]

  Delete mode used to delete CDF Groups, Datasets and Raw Databases, CDF
  Groups and RAW Databases will be deleted, while Datasets will be archived
  and deprecated (as they cannot be deleted).

Options:
  -h, --help  Show this message and exit.
```
### `Diagram` command

The diagram command is used to create a mermaid diagram to visualize the end state of a given configuration. This can be used to check the config file and to see if the constructed hiarchy is optimal. It is also very practical for documentation purposes.

```text
Usage: bootstrap-cli diagram [OPTIONS] [CONFIG_FILE]

  Diagram mode used to document the given configuration as a Mermaid diagram

Options:
  --markdown [yes|no]             Encapsulate Mermaid diagram in Markdown
                                  syntax. Defaults to 'no'
  --with-raw-capability [yes|no]  Create RAW DBs and 'rawAcl' capability.
                                  Defaults to 'yes'
  --cdf-project TEXT              [optional] Provide the CDF Project name to
                                  use for the diagram 'idp-cdf-mappings'.
  -h, --help                      Show this message and exit.
```
## Configuration

A YAML configuration file must be passed as an argument when running the program.
Different configuration file used for delete and prepare/deploy

### Configuration for all commands

All commands share a `cognite` and a `logger` section in the YAML manifest, which is common to our Cognite Database-Extractor configuration.

The configuration file supports variable-expansion (`${BOOTSTRAP_**}`), which are provided either as
1. environment-variables,
2. through an `.env` file or
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


#### Environment variables

Some more detail on the variables:

- BOOTSTRAP_CDF_HOST
  - The url to your cdf cluster. 
  - Example: ```https://westeurope-1.cognitedata.com```
- BOOTSTRAP_CDF_PROJECT
  - The CDF Project. 
- BOOTSTRAP_IDP_CLIENT_ID
  - Client id of the App Registration you have created for the CLI
- BOOTSTRAP_IDP_CLIENT_SECRET
  - Client secret created for the App registration
- BOOTSTRAP_IDP_TOKEN_URL= ```https://login.microsoftonline.com/<tenant id>/oauth2/v2.0/token``` 
  - In case you use Azure AD Replace ```<tenant id>``` with your Azure Tenant ID.
- BOOTSTRAP_IDP_SCOPES
  - Usually: ```https://<cluster-name>.cognitedata.com/.default```

### Configuration for `deploy` command

In addition to the sections described above, the configuration file for `deploy` command requires two more sections:

- `bootstrap` - declaration of the logical access-control group structure
- `aad_mappings` - mapping AAD Group object-ids with CDF Groups

#### `aad_mappings` section: AAD Group to CDF Group mapping

Used to link CDF Groups with AAD Groups.
Defines the name of the CDF Group, with the AAD Group object-id, and for documentation the AAD Group name.

Example:

```yaml
aad_mappings:
  #cdf-group-name:
  #  - aad-group-object-id
  #  - READABLE_NAME like the AAD Group name
  cdf:all:owner:
    - 123456-7890-abcd-1234-314159
    - CDF_DEV_ALL_OWNER
```

##### `bootstrap` section

The `bootstrap` section allows a two-level configuration of access-control groups:

Like for example:

- `src` for sources or `ca` for corporate applications,
- `in` for user-input control,
- `uc` typically for use-cases (providing the data-product and built on top of the other data-sources)

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

For a complete example of the `deploy` configuration, see `configs/test-bootstrap-deploy-example.yml`.

### Configuration for `delete` command

In addition to the `config` and `logger` sections described above, the configuration file for delete mode
should include one more section:

* `delete_or_deprecate` - used to define which CDF Datasets, CDF Groups and RAW databases (including tables) should to be deleted (CDF Datasets are in-fact only deprecated, as they cannot be deleted)

##### `delete_or_deprecate` section

This section defines what `datasets` that should be deprecated, and which `groups` and `raw_dbs` that should be deleted.

Example configuration:

```yml
delete_or_deprecate:
  # datasets: []
  datasets:
    - test:fac:001:name
  # groups: []
  groups:
    - test:fac:001:name:owner
    - test:fac:001:name:read
  # raw_dbs: []
  raw_dbs:
    - test:fac:001:name:rawdb
```

If nothing to delete, provide an empty list like this: `[]`.

**Tip:** After running the bootstrap in `deploy` mode, the final part of the output logs will include a "Delete template" section. This can be used for copy-paste the item names to the `delete` configuration.

For a complete example of the delete configuration, see the `configs/test-bootstrap-delete-example.yml`.

# Development / Contribute

1. Clone the repository and `cd` to the project folder.  Then,
2. initialize the project environment:

    ```sh
    poetry install
    ```

3. Install the pre-commit hook:

    ```sh
    poetry run pre-commit install #Only needed if not installed
    poetry run pre-commit run --all-files
    ```

## Inspiration

Templates (blueprints) used for implementation are
  - `cognitedata/transformation-cli`
  - `cognitedata/python-extratcion-utils`
    - using `CogniteConfig` and `LoggingConfig`
    - and extended with custom `dataclass` driven configuration

## Semantic versioning
- Uses `semantic-release` to create version tags.
- The rules for commit messages are conventional commits, see [conventionalcommits](https://www.conventionalcommits.org/en/v1.0.0-beta.4/#summary%3E)
- Remark: If version needs change, before merge, make sure commit title has elements mentioned on `conventionalcommits`
- Remark: with new version change, bump will update the version on `pyproject.toml` so no need to change version there.
- Remark: version in `incubator/bootstrap_cli/__init__` is used in main to add version on metadata.
  This is not a part of semantic release but needs to be updated to upcoming version before version update.


# Other ways of running
- it provides a configuration driven deployment for Cognite Bootstrap Pipelines (named `bootstrap` in short)
  - support to run it
    - from `poetry run` (explained in [Getting Started](#how-to-get-started))
    - from `python -m`
    - from `docker run` 
    - as GitHub Action (explained in [Getting Started](#how-to-get-started))
    - as Windows Executable (planned as feature-request)



Follow the initial setup first
1. Fill out relevant configurations from `configs`
  - Fill out `aad_mappings` and `bootstrap` from `test-bootstrap-deploy-example.yml`
  - Fill out `delete_or_deprecate` from `test-bootstrap-delete-example.yml`
2. For local testing, copy `.env_example` to `.env`
   - complete CDF and IdP configuration in `.env`
## run local with poetry

- some more information for running on native Windows / PowerShell / multiple Python versions can be [found here](POETRY_ON_WINDOWS.md)

> **WINDOWS USER:** the provided `pyproject.toml` and `poetry.lock` files are built to support "*nux" (MacOS, WSL2, Linux) first.
>
> On Windows (native, not WSL2) you have to delete the `poerty.lock` file first before you run `poetry install`.
>
> We have plans to support Windows with an executable, which eliminates the need for a Python installed too.


```bash
  # typical commands
  poetry build
  poetry install
  poetry update
```
- Deploy mode:
```bash
  poetry run bootstrap-cli --debug deploy configs/test-bootstrap-deploy-example.yml
```
- Prepare mode:
```bash
  poetry run bootstrap-cli --debug prepare configs/test-bootstrap-deploy-example.yml
```
- Delete mode:
```bash
  poetry run bootstrap-cli --debug delete configs/test-bootstrap-delete-example.yml
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
docker build -t incubator/bootstrap-cli:v1.0 -t incubator/bootstrap-cli:latest .

# ${PWD} because only absolute paths can be mounted
docker run --volume ${PWD}/configs:/configs --volume ${PWD}/logs:/logs  --env-file=.env incubator/bootstrap-cli deploy /configs/test-bootstrap-deploy-example.yml
```

Debug the Docker container
- requires override of `ENTRYPOINT`
- to get full functional `bash` a `Dockerfile.debug` is provided

```bash
➟  docker build -t incubator/bootstrap-cli:debug -f Dockerfile.debug .

➟  docker run --volume ${PWD}/configs:/configs --volume ${PWD}/logs:/logs  --env-file=.env -it --entrypoint /bin/bash incubator/bootstrap-cli:debug
```

