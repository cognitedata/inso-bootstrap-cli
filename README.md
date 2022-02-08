# scope of work

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

- [ ] `.pre-commit-config.yaml` hook support
- [x] `.dockerignore` (pycache)
- [x] logs folder handling (docker volume mount)
- [ ] logger.info() or print() or click.echo(click.style(..))
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
