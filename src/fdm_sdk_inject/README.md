## notes about fdm-inject

As of adding FDM / DMS scoping support to bootstrap-cli Cognite Python SDK doesn't support DMS v2 or V3 API requests.
The new scoping-element is named "space" and is handled very similar to the existing onws being "rawdb" and "datasets".

The "fdm_sdk_inject" provides a minimal implementation of the API requests necessary:
- DMS v2 implementation (used for a first proof-of-concept in Sep'22) in `data_model_storages` folder
  - v2 implemented data_class `space` with identifier `external_id`
- latest DMS v3 (which is planned for GA release) in `models` folder
  - v3 implemented data_class `space` with identifier `space`

As a code-template and folders-structure Cognite Python SDK `cognite/client/data_classes/transformations/jobs.py` was used.

### Bootstrap-CLI injects DMS v3 version into the `CogniteClient`

From `incubator/bootstrap_cli/app_container.py`

```py
#
# FDM SDK injector
#
client = CogniteClient(cnf)
_API_VERSION = "v1"
# if not getattr(client, "data_model_storages", None):
#     # DMS v2
#     client.data_model_storages = DataModelStoragesAPI(
#         config=client.config, api_version=_API_VERSION, cognite_client=client
#     )
#    logging.debug("Successfully injected FDM DMS v2 'client.data_model_storages'")
if not getattr(client, "models"):
    # DMS v3
    client.models = ModelsAPI(config=client.config, api_version=_API_VERSION, cognite_client=client)
    logging.debug("Successfully injected FDM DMS v3 'client.models'")
```
