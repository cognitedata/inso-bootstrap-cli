# version

# requires py>3.7
# from importlib_metadata import version as pyproject_version
# __version__ = pyproject_version("inso-extpipes-cli")
# print(f'__version__: {__version__}')

# keep manually in sync with pyproject.toml until the above approach is working in Docker too
# SOLVED: 220419 pa: switched to gh-action semantic-versioning, but still requires manually update here
# 230301 pa: automated by adding it to pyproject.toml > [tool.semantic_release] > version_variable

# 230802 pa: switched to manual updates, after issues with semver gh-actions
__version__ = "3.2.1"
