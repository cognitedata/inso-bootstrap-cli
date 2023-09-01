#
# 230327 pa: the Dockerfile is a full rework, to use the power of
# poetry, venv and wheels, the same way you work local
#
# inspiration: https://bmaingret.github.io/blog/2021-11-15-Docker-and-Poetry
#

ARG APP_NAME=inso_bootstrap_cli # matching the pyproject.toml name
ARG APP_PATH=/opt/$APP_NAME
ARG PYTHON_VERSION=3.11
ARG POETRY_VERSION=1.3.2

#
# Stage: staging
#
# gcr.io/distroless/python3-debian11 (runtime env is using 3.9 and that's important for native dependencies)
FROM python:${PYTHON_VERSION}-slim AS staging

# copy ATGs into stage
ARG APP_NAME
ARG APP_PATH
ARG POETRY_VERSION

ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1
ENV \
    POETRY_VERSION=$POETRY_VERSION \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# python-slim image is missing curl
RUN apt-get -y update; apt-get -y install curl

# Poetry setup
# RUN python3 -m pip install --upgrade pip
# RUN pip install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR $APP_PATH

COPY ./poetry.lock ./pyproject.toml README.md ./
# respecting .dockerignore and skips __pycache__ folders!
COPY ./src ./src

#
# Stage: development
#
FROM staging as development
ARG APP_NAME
ARG APP_PATH
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR $APP_PATH
RUN poetry install
ENTRYPOINT ["poetry", "run", "bootstrap-cli"]

#
# Stage: build
#
FROM staging as build
ARG APP_PATH

WORKDIR $APP_PATH
RUN poetry build --format wheel
RUN poetry export --format requirements.txt --output requirements.txt --without-hashes

#
# Stage: production
#
FROM python:${PYTHON_VERSION}-slim as production
ARG APP_NAME
ARG APP_PATH

ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

ENV \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Get build artifact wheel and install it respecting dependency versions
WORKDIR $APP_PATH
COPY --from=build $APP_PATH/dist/*.whl ./
COPY --from=build $APP_PATH/requirements.txt ./
RUN pip install ./$APP_NAME*.whl -r requirements.txt

# to allow reuse of logger-configs using ./logs/..
RUN mkdir  $APP_PATH/logs
# allow writing to logs
RUN chmod 666 $APP_PATH/logs