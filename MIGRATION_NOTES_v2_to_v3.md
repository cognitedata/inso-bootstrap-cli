## capabilities

- `threed` (3D) is now fully-scoped with datasets (was before `all` scoped)
  - in case you created `threed` resources **without** attaching it to a dataset, you need to update all your `threed` resources and assign a dataset.
  - after you have run `bootstrap-cli` with the latest v3 changes. this change can only be done by a service-account or user which is part of the `cdf:root` group

## configuration

### new

(support for new Cognite Data Fusion feature ["Data Modelling"](https://docs.cognite.com/cdf/data_modeling/))
- `bootstrap.features.with-datamodel-capability` default: `true`
- `bootstrap.features.space-suffix` default: `spc`

- `bootstrap.idp-cdf-mappings[].create-only-mapped-cdf-groups` default `true`
  - switch to only create CDF Groups which are mapped to an IdP.
    This is reducing the amount of created CDF Groups to the minimum.
    It is the defaultnow to only create CDF Groups, which have an effect.


### deprecated
- `bootstrap.features.with-special-groups` is not required in Cognite Data Fusion anymore


## cli

### changed

- `--dry-run` is now a simple flag and does not require a value anymore

### deprecated / removed
- `--with-special-groups`
- `--aad-source-id` as an alternative to `--idp-source-id`. Only latter is supported now.
