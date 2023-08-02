# CHANGELOG



## v3.0.2 (2023-08-02)

### Fix

* fix: depandabot (#88)

* fix: depandabot
- closing #86 and #84

* fix: changelog linting (created by semver)

* fix: poetry update to 1.5.1 ([`5b657f0`](https://github.com/cognitedata/inso-bootstrap-cli/commit/5b657f0b77528013f1e3101371e8d0ad011de026))


## v3.0.1 (2023-08-02)

### Fix

* fix: command &#34;prepare&#34; regression (#87)

* fix: prepare regression
- which uses CogniteDeployedCache with `groups_only` mode
- but refactored `log_counts` method was not respecting it

* fix: CommandBase init fix
- doesn&#39;t need config unpacking for `CommandMode.PREPARE`
- it only requires the `CogniteContainer` for instantiating a client ([`ea5884b`](https://github.com/cognitedata/inso-bootstrap-cli/commit/ea5884b3ad1aad8b7df31de39d1839d959c1b51d))

### Unknown

* automatic semver release failed (#82)

latest v3.0.0 release was semi-automated, as this gh-action had a bug from migration

- changed `::set-output` to `&gt;&gt; $GITHUB_ENV`
-  simply use GITHUB_ENV with access like `env.match == &#39;true&#39;`
- using  `steps...outputs...` requires `&gt;&gt; $GITHUB_OUTPUT`
  - recommended for inputs/outputs/needs between *jobs*
  - but not necessarily *steps* where shared GITHUB_ENV is sufficient
- just decide which approach to follow ([`260f661`](https://github.com/cognitedata/inso-bootstrap-cli/commit/260f661e99b0f4402ffd24d3e1153e0b34aced1c))


## v3.0.0 (2023-07-04)

### Breaking

* feat: v3 bump (#81)

BREAKING CHANGE: new features, slightly changed config
- support added for `space` scoped capabilities
  - dataModelsAcl &amp; dataModelInstancesAcl
- cleanup and changes to configuration syntax (breaking)
  - more of an light improvement, not a radical change
- refactored code-base for easier collaboration and contributions
- moved to py3.11, SDK v6.2, pydantic, dependency-injection
- gh-action benefits from pre-built images published on docker-hub
  - built using buildpacks
- MIGRATION notes and README updated

for details check PR #75 ([`8127595`](https://github.com/cognitedata/inso-bootstrap-cli/commit/81275959007dd303eae984fbbbdc6551415be271))

* feat: v3 bump (#80)

BREAKING CHANGE: full code overhaul, new features, slightly changed config
- support added for `space` scoped capabilities
  - dataModelsAcl &amp; dataModelInstancesAcl
- cleanup and changes to configuration syntax (breaking)
  - more of an light improvement, not a radical change
- refactored code-base to ease collaboration and contributions
- moved to py3.11, SDK v6.2, pydantic, dependency-injection
- gh-action benefits from pre-built images published on docker-hub
  - built using buildpacks
- MIGRATION notes and README updated

for details check PR #75 ([`8d740f4`](https://github.com/cognitedata/inso-bootstrap-cli/commit/8d740f42e342442e17e66149ead62263d74fd6dd))

### Unknown

* BREAKING CHANGE: V3beta3 (#75)

* BREAKING CHANGE: v3 release
- support added for `space` scoped capabilities
  - dataModelsAcl &amp; dataModelInstancesAcl
- cleanup and changes to configuration syntax (breaking)
  - more of an light improvement, not a radical change
- refactored code-base to ease collaboration and contributions
- moved to py3.11, SDK v6.2, pydantic, dependency-injection
- gh-action benefits from pre-built images published on docker-hub
  - built using buildpacks
- MIGRATION notes and README updated

* refactor approach
- dependency-injector &gt; app_container
- pydantic rewrite &gt; app_config
- Python SDK &gt; app_container.get_cognite_client
- test cases

* feat(migration): dry-run tested command-modes
- extended test cases

* feat(spaces): started merge of sep&#39;22 implementation of FDM support

* fix(fdm): changed to fdm-sdk-inject /models (DMS v3)
- minimized to functions used (create, list, delete)
- group acls still using v2 scopes, v3 not available yet

* fix(mermaid + acls): added more acls
- roboticsAcl, extractionConfigsAcl
- fixed most diagram issues with `spaces`
- WIP: simplified diagram with dataset only, needs another config than `--with_raw-capability no`
- WIP: is moving threedAcl from &#34;only-all-scope&#34; to datasetScope a breaking change?

* fix(code-structure): major refactoring
- refactored commands into modules
- refactored into app_cache
- dropped finnaly deprecated configuration.py based on dataclasses

* fix(pre-commit): run for all files
- marked a few too long with `# noqa` which are hard to split lines

* fix(naming): mostly renaming
- `semantic_release` fix maybe helping for keeping version up to date automatically

* fix(dms-v3): activating v3 scopes (space-create uses v3 too)

* fix(rawdb-delete): removed recursive=True
- added TODO to validate non-empty rawdbs first
- and maybe allowing a &#34;force&#34; switch

* fix(fdm-inject): add readme and fix  injection test to v3 `models`

* fix: backport regression fix for `validate_config_shared_access`  from v2.5.1
- adding default to getattr() check

* fix: poetry.lock recreated after `git merge main`

* fix(pre-commit): support for latest flake8 v6 with `.flake8` config
- support for black parsing py3.10 `match` command

* fix: spaces.delete fixed payload

* fix: changed abs to to relative imports
- moved diagram into a &#39;diagram_utils&#39; package

* big changed of folder structure to classic `src`
- makes tracing of changes hard :(
- added `common` with base_model *for pydantic)
- and cognite_client
  - should be the same for  all projects
  - sadly bootstrap/extpipes/transformations use an idp-subsection, instead of a flat properties `cognite` config
- sharing same code structure with next extpipes-cli v3

* fix accidental changes

* fix: changing again src/ sub-folder structure
- making `bootstrap` and `fdm_sdk_inject` parallel packages
- define `packages` in pyproject.toml
- change pytest &gt; test_app_config.py, to import `from bootstrap import **`

* fix: docker build switched to proper multistage
- support targets: staging, development, build and production

* fix: dry-run is a flag, api-key references removed

* fix: dry_run bugs after change to flag
- making it optional for diagram

* fix: removed `with-special-groups` support for v3

* fix: renamed &#34;action&#34; to &#34;role_type&#34;
- to match the bootstrap-cli &#34;RoleType&#34; enum (OWNER, READ)
- to distinguish from real cdf-actions like READ, WRITE, UPDATE

* fix: hidden bug
- bug was that  `{ns}:all:owner` groups got shared-access from all its nodes
- but aggregated (`all`) groups don&#39;t support shared-access by design
- error become obvious with duplicate `spaceIds` created in one project test

* fix: typehint cleanup
- migrated mermaid.py to pydantic
- still not all pylance oddities fixed

* feat: added support to **limit** CDF Groups creation
-  to only those with an existing IdP mapping
- configurable per project in
  `bootstrap.idp-cdf-mappings[].create-only-mapped-cdf-groups`

feat: included CDF Group `metadata` support to store additional info
  - like the removed idp `source` name (~Dec&#39;22 from API v1)
  - code needs an update when SDK supports `metadata` native

fix: extended test coverage for new config options

* fix: diagram code after pydantic change
- next step: implement to diagram nodes with IdP mapping only
- supporting: `create_only_mapped_cdf_groups` parameter

* fix: rework create_groups to store created groups
- prepare migrates using idp-maping dataclass
- prepare / deploy needs testing

* fix: refactored code for diagram into multiple methods

* fix: readme, migration notes
- changed some cli defaults to `api` (before `westeurope-1` or `bluefield`

* fix: updated dependencies
- bumped setuptools to latest v67.*

* fix: linting

* fix: minor README changes how to run bootstrap-cli locally

* fix: more README changes

* fix: changed one `&#34;&#34;.format()` to `f&#34;{}&#34;` string
- all other `.format(..)` occurrences are required
   as they use predefined (named) f-string-templates

* fix: `create-only-mapped-cdf-groups` default is true
- new default for v3
- changed example config, readme, migration notes

* feat: start builderpack image build and push

* fix(fdm-sdk-patch): removed
- replaced by official Python SDK v6.2.1 release!

* fix(python-version): updated to 3.11
- required `Enum` to be replaced by `ReprEnum` to keep f-string working
- updated gh-action, dockerfile, poetry, pre-commit py versions
- more changes to use official `client.data_modelling.spaces`
- wip: Dockerfile to support ./logs folder for file-logging

* fix: fixing deprecated gh-action set-output
- add run.sh for buildpack testing

* fix(readme): docker run now works
- for logger-configs configured for `./logs/..`

* fix(spaces): `create` replaced by `apply`
- which is the new way to support &#34;patching&#34;

* feat(ci): adding CI using buildpack
- publishing to dockerhub
- goal is speed up gh-action using the already built image

* fix: adding pack/runs.sh
- experimental

* fix(gh-action): same as in main
- hopefully  fixing the problem
```
Workflow does not exist or does not have a workflow_dispatch trigger in this branch.
```

* fix: try to run them on branch w/o merge to main?

* fix: change ci name as two appeared in gh-ui

* fix: roll back ci name change

* fix: renamed ci.yml to .yaml to match main branch

* fix: add setup-pack depenendcy to gh-action

* fix: trying with `docker://` removed from image

* fix: support config-file loading
- when running as GITHUB_ACTIONS
- loading relative from  `/github/workspace` folder

* fix: adopt `action.yaml` to
docker://cognite/bootstrap-cli:v3.0.0-beta.3-github

* fix: prepare v3.0.0 in action.yaml
- updating README section about buildpacks
- removed outdated poetry/windows instructions

* fix: remove unused

* fix: gh pre-commit
- changed pre-commit/action to poetry based pytest / pre-commit / check

* fix: gh-actions
- linting and removed unnecssary `poetry keyring`

* fix: silenced prints in pytest

* fix: deact ci trigger from pull-request
- only manual `workflow_dispatch` trigger ([`8920e54`](https://github.com/cognitedata/inso-bootstrap-cli/commit/8920e54b9040170e832a7df4e396283a4cce5a4e))

* no release, only adding `on: pull_request` to ci.yaml (#79)

- hopefully allowing testing from branches
- ci in main branch only logs ([`3f209bc`](https://github.com/cognitedata/inso-bootstrap-cli/commit/3f209bc9c24de50db0cf2a6e3f72cddf46065328))

* testing ci gh-action (#77)

- no semver release ([`c4c5732`](https://github.com/cognitedata/inso-bootstrap-cli/commit/c4c57328b157befd2d89b22c2a415676436af626))

* adding ci.yaml for testing (#76)

- no semantic release
- seems gh-actions cannot be tested from branch
- related to branch: `v3beta2` ([`99a7453`](https://github.com/cognitedata/inso-bootstrap-cli/commit/99a74535db4a29781ae0bdcc08acf7d13ed7b67b))


## v2.7.0 (2023-04-19)

### Feature

* feat(acl): added robotics (#73)

* feat(acl): added robotics
- with dataset-scope support

* fix: resolving and closing issue #72

* fix: depandabot alert #61
- bumped setuptools to latest ^67 ([`2cc2bc4`](https://github.com/cognitedata/inso-bootstrap-cli/commit/2cc2bc45e68b8c2004f67a86f867fef98e0e8d7b))


## v2.6.0 (2023-03-20)

### Feature

* feat: adding annotationsAcl support (#70)

- supporting all actions
- even if `action:REVIEW` seems not to be used atm
- and `action:READ` is implicit ([`3a65096`](https://github.com/cognitedata/inso-bootstrap-cli/commit/3a65096e36b03494586f80f9a0d2afc9bfb20b3f))


## v2.5.1 (2023-03-01)

### Fix

* fix(dockerfile): required bump to py3.10 too (#69)

- readme update, as __init__ is now covered by SemVer ([`9156bc8`](https://github.com/cognitedata/inso-bootstrap-cli/commit/9156bc83885597ef466201ef3da7db1e39288a0f))


## v2.5.0 (2023-03-01)

### Feature

* feat: version in init and pyproject.toml seems to be in sync that SemVer can bump them in gh-action (#67)

#66 contains all the relevant changes
this one is just trying to bump the semantic-versioning ([`044510c`](https://github.com/cognitedata/inso-bootstrap-cli/commit/044510c9233d5ceaa181dceb18f909ae4eca2a83))

* feat: Fix validation regression and adding new acl support (#66)

* fix(dependency): bumped to py3.10
- bumped isort to 5.12.0 (in pyproject and pre-commit-config!) to fix known `RuntimeError: The Poetry configuration is invalid`

* feat(acl): extractionConfigsAcl added to list of scoped ACLs
- regression fixed in `validate_config_shared_access()` which missed shared-access support for aggregated-nodes lie `src:all`

* fix(gh-action): bumped action versions
- pumped py to 3.10

* fix(gh-action): pre-commit requires `v3.0.0` instead of only `v3`? ([`a0b860c`](https://github.com/cognitedata/inso-bootstrap-cli/commit/a0b860ccd8e1a13456551444d25cc8850365b84d))


## v2.4.0 (2023-01-10)

### Feature

* feat(validation): adding shared-access validation (#62)

* feat(validation): adding shared-access validation
- for `diagram` and `deploy`
- abort with `BootstrapValidationError` if a shared-access node-name does not exist in config ([`dbd4c00`](https://github.com/cognitedata/inso-bootstrap-cli/commit/dbd4c00ebd5c108e83624e04f253d00b95549796))

### Unknown

* remove disclaimer (#59) ([`b20249d`](https://github.com/cognitedata/inso-bootstrap-cli/commit/b20249d85573e22040005ee8aced0bc0d08b6f51))


## v2.3.0 (2022-11-21)

### Feature

* feat(acls): adding `wells` capability

- Resolve #57 - add wells capability
- bumped version to 2.3.0
- fixed failing pre-commit, because flake8 switched from gitlab to github
- aligned flake8 version with latest used in transformation-cli

Co-authored-by: Peter Arwanitis &lt;spex66@gmx.net&gt; ([`ae0a892`](https://github.com/cognitedata/inso-bootstrap-cli/commit/ae0a8927b770cf47f4d0c912ee838000bad9ac9a))


## v2.2.1 (2022-09-26)

### Fix

* fix(oauthlib): Bump oauthlib from 3.2.0 to 3.2.1 (#56)

* Bump oauthlib from 3.2.0 to 3.2.1
(locally run a `poetry install` to get the update)

Bumps [oauthlib](https://github.com/oauthlib/oauthlib) from 3.2.0 to 3.2.1.
- [Release notes](https://github.com/oauthlib/oauthlib/releases)
- [Changelog](https://github.com/oauthlib/oauthlib/blob/master/CHANGELOG.rst)
- [Commits](https://github.com/oauthlib/oauthlib/compare/v3.2.0...v3.2.1)

---
updated-dependencies:
- dependency-name: oauthlib
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

* fix(oauthlib): bump version number for semver

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt;
Co-authored-by: Peter Arwanitis &lt;peter.arwanitis@cognite.com&gt; ([`54ee8da`](https://github.com/cognitedata/inso-bootstrap-cli/commit/54ee8da4f19d533d0d1766a229e3cf924efc244c))

### Unknown

* Minor clarification on shared access scopes. (#54)

* Minor clarification on shared access scopes.
- added a new section about &#34;How tos&#34;
- added a chapter about read-only access-control groups
- refactored internal discussion and comment from issue #33

Co-authored-by: Peter Arwanitis &lt;peter.arwanitis@cognite.com&gt; ([`b27d5c3`](https://github.com/cognitedata/inso-bootstrap-cli/commit/b27d5c3748405b103561cbb65cbc927d39c2b354))


## v2.2.0 (2022-08-31)

### Feature

* feat(acls): added four new acls

- Joel: Added `templateGroups` + `templateInstances` to `acl_default_types` (with dataset support)
- feat(acls): Peter added two more acls for FDM support `dataModels` + `dataModelInstances`
  - &#34;all&#34; scope for now, as `externalId` scope is not supported yet, and hopefully will change before GA
  - acls expected not to harm if FDM is not activated
- bumped version number to new 2.2.0

Co-authored-by: Sirefelt &lt;joel.c.sirefelt@accenture.com&gt;
Co-authored-by: Peter Arwanitis &lt;peter.arwanitis@cognite.com&gt; ([`5727dc2`](https://github.com/cognitedata/inso-bootstrap-cli/commit/5727dc21d8ad62f6fbffb6f572aecfbcbd391cc6))


## v2.1.0 (2022-08-09)

### Feature

* feat(acls): adding four acls (#51)

- added acls with all-scope ([`695cd81`](https://github.com/cognitedata/inso-bootstrap-cli/commit/695cd8103077a56bd76cc8305ae0d425befbfa17))


## v2.0.3 (2022-08-09)

### Fix

* fix: Refactor deployed config caching (#50)

* refactored load_deployed_config_from_cdf

* refactored CogniteResourceCache and improved dry-run logging
- tested against tranding-playground

* logger changes:
- switched a lot logs to debug
- tested &#39;prepare&#39; mode with latest changes

* fix: logging and internal caching
- mostly a code cleanup (removed explicit chunking as SDK handles it)
- lots of logs switched to debug-level (configure level in config yaml!, the `--debug` flag is not working)
- cleaned up dry-run logging and potentially fixed isses with `delete` and `prepare` command
- new `CogniteResourceCache` and `CogniteDeployedCache` to track deployed CDF resources
  - looks now like an overkill to replace the -- sometimes buggy -- time.sleep() and reload from CDF

* fix(logging): finally made the `--debug` flag working

* small comment changes ([`ffffc4a`](https://github.com/cognitedata/inso-bootstrap-cli/commit/ffffc4a4df26f7d8059d37a303b263a1586a5b57))

### Unknown

* Merge pull request #49 from cognitedata/offboarding-june

Update pyproject.toml ([`688beca`](https://github.com/cognitedata/inso-bootstrap-cli/commit/688beca0b7fd651d0e34cf842dd085d6ef4c6df0))

* Update pyproject.toml ([`f8ceb5f`](https://github.com/cognitedata/inso-bootstrap-cli/commit/f8ceb5f83acb362accf16a5cd016eaa80dd91d67))


## v2.0.2 (2022-07-01)

### Fix

* fix(text review): comments, example and readme (#48)

* text review

* Rewrite intro paragraphs + replacing &#34;data set&#34; with &#34;dataset&#34;

* updated Readmy TOC and transfered readme-improvements to help-texts in __main__.py

* Text review

* changed from Raw/raw database-&gt; RAW database

Co-authored-by: Sverre Dørheim &lt;sverre.dorheim@cognite.com&gt; ([`ac13f8a`](https://github.com/cognitedata/inso-bootstrap-cli/commit/ac13f8a3b6ab85bffafbf926a28991cb374a6fd4))

### Unknown

* added figlets (banner) comments (#46)

- easy navigation for mini-preview ([`d2ed0e5`](https://github.com/cognitedata/inso-bootstrap-cli/commit/d2ed0e575703acc7af2a11212357b6fd439f5279))

* restore deleted chapters (#45)

* restore deleted chapters

- fixed more config example file renames
- removed `--debug` flag from examples for brevity ([`940d170`](https://github.com/cognitedata/inso-bootstrap-cli/commit/940d1705045792a1f35aa0abe0326f4e4b58b9ce))

* Updated example config to use recommended settings instead of defaul,… (#43)

* Updated example config to use recommended settings instead of default, rewrote a bit and added sections to the Readme
* Updated readme: Added Azure setup and updated Github Actions example yaml
* Fixed a few typos
* Spell-check + leftover V1-config references
* some consistency-fixes
* cleaned up configs folder files
- removed outdated examples
- updated references
* plain English

Co-authored-by: Joergen Wessel &lt;joergen.wessel@cognite.com&gt;
Co-authored-by: Peter Arwanitis &lt;peter.arwanitis@cognite.com&gt; ([`73133d1`](https://github.com/cognitedata/inso-bootstrap-cli/commit/73133d16f9bdb06021640e0d12267128714fa7eb))


## v2.0.1 (2022-05-19)

### Fix

* fix(deploy): same logic for project with no  rawdb (#44)

* patch(deploy): same logic for project with no  rawdb
- as done for datasets before
- create an empty dataframe, but with defined list of columns
- that following code is not failing on sorting and dump

* patch version bump to 2.0.1 ([`b338a10`](https://github.com/cognitedata/inso-bootstrap-cli/commit/b338a10d81408ddf3e87ee09d157af997682fbc7))


## v2.0.0 (2022-05-11)

### Breaking

* feat(syntax): release v2 configuration syntax (#41)

BREAKING CHANGE: new configuration yaml sytnax
- documentation for this is planned next
- if you want to continue with v1 syntax use `v1.10.1` release ([`4f6b77b`](https://github.com/cognitedata/inso-bootstrap-cli/commit/4f6b77bb7b1b64e669642b3f2ff33ae9348c0dee))

### Unknown

* BREAKING CHANGE: next try to trigger bump ([`fc3d7e7`](https://github.com/cognitedata/inso-bootstrap-cli/commit/fc3d7e73ae67c3de9e6bd6d2b9811c815d77b815))

* BREAKING CHANGE: bump to v2.0 (#40) ([`2f35d38`](https://github.com/cognitedata/inso-bootstrap-cli/commit/2f35d38764a35e6ade84b217b71ddc3e86b0fe86))

* BREAKING CHANGE: V2 syntax change (#32)

* v2 syntax migration
- deploy and diagram commands
- test v1 and v2 configs
- separate config module for dataclasses

* for &#39;diagram&#39; command
- made &#39;cognite&#39; section optional
- added support for parameter &#39;--cdf-project&#39;
  to explicit diagram a specific CDF Project from idp-cdf-mappings
- reflect cdf-project name in &#34;IdP Groups for CDF: &lt;&gt;&#34; subgraph title
- renamed mermaid properties from &#39;name/short&#39; to &#39;id_name/display&#39;

* documented v2 config

* new CommandMode enum
- made &#39;cognite&#39; section optional for &#39;diagram&#39;
- tested &#39;diagram&#39; with v2 and new parameters
- only tested &#39;deploy&#39; in dry-run
- not tested &#39;prepare&#39; and &#39;delete&#39;

* README and cli-help text updates

* fixing mermaid subgraph titles
- providing enum.value as short_name to display

* comments and preparing improved mermaid
- adding allprojects datasets and rawdbs

* fixed `with_raw_capability` default is `True`

* removed defaults from click-options
- `--with-special-groups`
- `--with-raw-capability`
- as they are provided now in `BootstrapFeatures` dataclass
- but can be overriden by cli-parameter

* added documentation for supported values for
- `with-special-groups`
- `with-raw-capability`

* - yaml added more comments
  - about `external-id` usage
- fixed `delete` and `prepare` command initialization
- added `--idp-source-id` parameter for `prepare` command
  - alternative for `--aad-source-id`
  - which is marked for deprecation

* now fixed `delete` command
- tested with `--dry-run yes`

* extended &#39;diagram&#39; to include
- generated namespace and top-level scopes too
- like `src:allproject:rawdb` or `allprojects:dataset`

* Syntax fix

Fixing syntax in the delete function

* bug fix `diagram` command
- handling different `with_raw_capability` options
- cli, yaml-config or default

* updated config-example features section
- adding hints which features support empty &#34;&#34; strings
- added support (deploy/diagram) to support empty-strings in such case

* support for empty-strings of features:
- group-prefix
- dataset-suffix
- rawdb-suffix

added new validation
- validate_config_length_limits

* comment in config-example

* updating version to 2.0.0

* fixed mermaid &#34;node level&#34; subgraph

* and same for read

Removing the parameters from gh action since they will be coming from the yaml file directly

* Update action.yml

Rollback

* Update action.yml

* more inline documentation (comments) added
- to simple-v2 configuration yaml

* more diagram/mermaid tips added

* moved `setuptools`
- from `tools.poetry.dev-dependencies`
- to dependencies
- to fix windows `poetry install` bug

* switched (back) to Linux support for poetry

* added Windows poetry and EXE section

* removed duplicate code
- and out commented code from testing

* built poetry.lock for linux again

* fixed sorting issue for groups or datasets
- with empty names
- reproduced issue
- added &#39;fillna(&#39;&#39;)&#39; in between

* resolved conversations
- replaced all `assert` statements
- used BootstrapConfigError and BootstrapValidationError (new)

* - refactored config and validation exceptions
  - into configuration.py
- added comment on internal acl/action configs

* few more inline comments

* final inline changelog change before v2.0.0 merge

Co-authored-by: Gaetan Helness &lt;gaetan.helness@cognite.com&gt;
Co-authored-by: Sverre Dørheim &lt;sverre.dorheim@cognite.com&gt;
Co-authored-by: Peter Arwanitis &lt;peter.arwanitis@cognite.com&gt; ([`2914c3d`](https://github.com/cognitedata/inso-bootstrap-cli/commit/2914c3d3e2890782390bb06fddacffb0e38cdf06))


## v1.10.1 (2022-04-25)

### Fix

* fix: adding-raw-parameter-github-action (#31)

* add new cli parameter `--with-raw-capability` support to github-action as `with_raw_capability` ([`b095a9a`](https://github.com/cognitedata/inso-bootstrap-cli/commit/b095a9ab3abee9d46df3045245030747451a2e63))


## v1.10.0 (2022-04-22)

### Feature

* feat: adding --with-raw-capability flag (#29)

* feat: adding `--with-raw-capability` flag
- for `deploy` and `diagram` commands

* updating click-parameter hints
- update README.md
- fixed &#39;pipenv&#39; typo in poetry-windows write-up =&gt; meant &#39;pyenv&#39;

* added formatting and comments for &#39;diagram&#39; ([`59ef482`](https://github.com/cognitedata/inso-bootstrap-cli/commit/59ef482ab4302788d5b9287f8e26696e31456454))


## v1.9.2 (2022-04-20)

### Fix

* fix: adding setuptools to dev-dependencies (#27)

* fix: adding setuptools to dev-dependecies
- required on winodws to build flake8
- bump to 1.9.2

* add poetry-windows learnings
- before we found a better place

* structure and phrases ([`893e627`](https://github.com/cognitedata/inso-bootstrap-cli/commit/893e627f9841de41cf8fe03f11b52a9317ea5573))


## v1.9.1 (2022-04-20)

### Fix

* fix: fixed outdated extractor-utils version (#26)

- which pulled in full cognite-sdk
- instead of sdk-core only
- which made installation on Windows too complicated ([`c0bb469`](https://github.com/cognitedata/inso-bootstrap-cli/commit/c0bb469f1f2deedcb5068872ddc63dab984b0157))


## v1.9.0 (2022-04-19)

### Feature

* feat: bump to 1.9.0 ([`8c4622a`](https://github.com/cognitedata/inso-bootstrap-cli/commit/8c4622a1be622ef802c1248bd0c3e12d6bc3f5fa))

### Unknown

* Removed loading of unnecessary data from CDF + cleanup (#25)

* Removed loading of datasets and rawDBs for Prepare-method (would fail)
Removed loading of CDF-config for Diagram as it is not needed

Also reformatted some of the logging when using dry-run, increasing information level on debug-level, and decreasing for info-level

* refactored load_deployed_config_from_cdf
- for better readability
- reducing repeated CDF API calls

* bumped version to next minor v1.9.0 as it is changing a method interface

Co-authored-by: Peter Arwanitis &lt;peter.arwanitis@cognite.com&gt; ([`ee989a4`](https://github.com/cognitedata/inso-bootstrap-cli/commit/ee989a4d69ff7545c83f2bf5fafb1c02376f14e3))

* Merge pull request #22 from cognitedata/readme-rework-v0.1

Readme rework v0.1 ([`cb6d6ec`](https://github.com/cognitedata/inso-bootstrap-cli/commit/cb6d6ec5c03696a7043ef3dea087370a6026f755))

* removed bold-format from headers ([`36f0250`](https://github.com/cognitedata/inso-bootstrap-cli/commit/36f0250fc15491e5cb1a74a127c6abfa02f5faf4))

* pa changes ([`2f9439c`](https://github.com/cognitedata/inso-bootstrap-cli/commit/2f9439ced9891b7eeec751fe3332a1d8aa2e8419))


## v1.8.0 (2022-04-07)

### Feature

* feat: added `threed` acl (#24) ([`fb4ffe1`](https://github.com/cognitedata/inso-bootstrap-cli/commit/fb4ffe157f4b460956cc5bb04e7e1b89115023fa))

### Unknown

* Merge pull request #23 from cognitedata/fixing-parameter-order-for-gh-action

fix: Fixing &#39;--debug&#39; parameter order in gh action ([`4fed10e`](https://github.com/cognitedata/inso-bootstrap-cli/commit/4fed10ec44f374912bd8242ba73db481e13d4dcd))

* moved `--debug` parameter before command `deploy`
- as it is now a global parameter for all commands ([`449bba7`](https://github.com/cognitedata/inso-bootstrap-cli/commit/449bba7ceb2823a0b3162c07ca5724cf7781fb01))

* changed usage of `--debug` parameter
- which now has to come before command (like `deploy`) ([`8e48b01`](https://github.com/cognitedata/inso-bootstrap-cli/commit/8e48b0149b9088b604049b3c4f422e51ba6e63eb))

* mermaid inline comment about edges added ([`03837ff`](https://github.com/cognitedata/inso-bootstrap-cli/commit/03837ff76895a40445ac9655bd9e9245cab85de4))

* added isort config
- profile = &#34;black&#34; ([`e34118a`](https://github.com/cognitedata/inso-bootstrap-cli/commit/e34118abd0ac6839f3fa16eb225d786844d68c67))

* Improved concept-section and some minor improvements to the rest of the readme, up until the configuration section ([`6bb3fee`](https://github.com/cognitedata/inso-bootstrap-cli/commit/6bb3fee32bfa2798f26c71005bdaba76cfdbfb6e))

* Merge remote-tracking branch &#39;origin/main&#39; into readme-rework-v0.1 ([`9623811`](https://github.com/cognitedata/inso-bootstrap-cli/commit/9623811e1f0c851b040ff7b29052e1a9d3012350))

* reworked mermaid chart a bit ([`5a974f4`](https://github.com/cognitedata/inso-bootstrap-cli/commit/5a974f422b1178c3e3bf9b13cd94ad93d0276b35))


## v1.7.1 (2022-04-06)

### Fix

* fix: change secret name, use bot email for sem ver (#21)

* Change secret name

* use bot email ([`0ee27cb`](https://github.com/cognitedata/inso-bootstrap-cli/commit/0ee27cbcc060bf6b7fd83cef2afa71f9ce55eefa))

### Unknown

* Merge pull request #20 from cognitedata/adding-semver-and-more-code-quality-checks

patch: Adding semver and more code quality checks ([`19bd020`](https://github.com/cognitedata/inso-bootstrap-cli/commit/19bd02038a33e3afbc3c8228e39d524b9b1b7634))

* fix isort checks. mypy checks still failing ([`7391ab9`](https://github.com/cognitedata/inso-bootstrap-cli/commit/7391ab9597ed151fd22c1b1d4cf96b9b1339fa33))

* Update pre-commit action ([`a0b7e15`](https://github.com/cognitedata/inso-bootstrap-cli/commit/a0b7e15b1ca7a8727d51bdf929b68ef70d4d12d2))

* Updare pre-commit action ([`0f73a14`](https://github.com/cognitedata/inso-bootstrap-cli/commit/0f73a14b786438b9b66785b2772108ec51dbceac))

* version 3.9 ([`13bf135`](https://github.com/cognitedata/inso-bootstrap-cli/commit/13bf135f1108323e0aa633b70818d95ed34a6701))

* compact code quality checks, updare README ([`75fcdd0`](https://github.com/cognitedata/inso-bootstrap-cli/commit/75fcdd0a311fe76bc7e608716dfdb7f44051494e))

* more code-quality checks
- using #fix: skip to stop black from formatting intended indented code ([`8e501cd`](https://github.com/cognitedata/inso-bootstrap-cli/commit/8e501cd901540046bcc16f334180bddabc7740cc))

* semver added ([`8ca9b64`](https://github.com/cognitedata/inso-bootstrap-cli/commit/8ca9b64fada7294bbb8203d6440fe2294c516dc7))

* Merge remote-tracking branch &#39;origin/main&#39; into readme-rework-v0.1 ([`a0dcfbd`](https://github.com/cognitedata/inso-bootstrap-cli/commit/a0dcfbdeb0e40e6ecaa3b396da5e3df7c01b4789))


## v1.7.0 (2022-04-06)

### Unknown

* Merge pull request #19 from cognitedata/doc-as-mermaid

&#34;Doc as mermaid&#34; which is one step towards a &#34;documentation&#34; feature (see issue #15 )

option 1: copy mermaid output to (Windows) `clip.exe` and copy it into `https://mermaid.live` for review
```
➟  poetry run bootstrap-cli diagram .local/config-deploy-bootstrap.yml | clip.exe
```
option 2: add a markdown wrapper and pipe it into a `graph.md` document, where you can use VSCode with mermaid extension as output or for review
```
➟  poetry run bootstrap-cli diagram --markdown-yes .local/config-deploy-bootstrap.yml &gt; graph.md
``` ([`d86bcc4`](https://github.com/cognitedata/inso-bootstrap-cli/commit/d86bcc4b1d26d25887e06b58c7cec52982cbda4e))

* changelog and version bump to 1.7.0 ([`978f6fd`](https://github.com/cognitedata/inso-bootstrap-cli/commit/978f6fd38ecfc60d86380bef5a76f865482330b5))

* more pre-commit cleanups ([`67cbd6d`](https://github.com/cognitedata/inso-bootstrap-cli/commit/67cbd6d006817192ed366455c010945f77bd7c0f))

* refactored again
- only Mermaid related in mermaid.py
- all bootstrap related building of a mermaid back in __main__.py
- markdown-wrapper option added outside mermaid logic ([`011bc14`](https://github.com/cognitedata/inso-bootstrap-cli/commit/011bc14c09a296e8444ed538b4e4297006b46db8))

* simple refactoring of mermaid generation + markdown option
Also reformatting through commit-hooks ([`ddedc4d`](https://github.com/cognitedata/inso-bootstrap-cli/commit/ddedc4d567b2e504e7be1cb03eed010871fbdfad))

* Merge remote-tracking branch &#39;origin&#39; into doc-as-mermaid ([`749d0fb`](https://github.com/cognitedata/inso-bootstrap-cli/commit/749d0fb679deabd3caf6d2e8c71cc3bb496284c0))

* Merge pull request #18 from cognitedata/refactor-names

Refactor names ([`7faea58`](https://github.com/cognitedata/inso-bootstrap-cli/commit/7faea58608a2dba5b8b360fb56ca2f9f4f3d9697))

* forgot the changelog on top
- to document the dimension&gt;hierarchy change ([`6d19a3e`](https://github.com/cognitedata/inso-bootstrap-cli/commit/6d19a3e8131416f5eabd7eec7edb6bba2bf8c46e))

* &#39;dimensions&#39; replaced through &#39;hierarchy&#39; ([`f7fb4e3`](https://github.com/cognitedata/inso-bootstrap-cli/commit/f7fb4e3bd4ba6b9d3ad3fc458726fc5f49ac1132))

* cleaned up comments with
-  `shared_global_config` occurences ([`0f11bbd`](https://github.com/cognitedata/inso-bootstrap-cli/commit/0f11bbdcc11b5a6862e039ac88b1ceea99ae317a))

* &#39;diagram&#39; command added ([`1dc93a5`](https://github.com/cognitedata/inso-bootstrap-cli/commit/1dc93a5851e0422f8d6880df833133166671b63c))

* comments ([`a88605f`](https://github.com/cognitedata/inso-bootstrap-cli/commit/a88605f080301c5632024d88577d83dad32ca50c))

* bump version to v1.6.0 ([`c620910`](https://github.com/cognitedata/inso-bootstrap-cli/commit/c620910568c908f785aebf4f24ba2d5c1374eaea))

* Merge v1.5.0 branch &#39;main&#39; into refactor-names ([`b1bb404`](https://github.com/cognitedata/inso-bootstrap-cli/commit/b1bb4043b2a9321504c9b88c382443ca459e48dc))

* Merge pull request #17 from cognitedata/dry-run-v0.1

resolving issue #13
- added basic dry-run capabilities
- fixed click-library to 8.0 do to 8.…
- moved `--debug` and `--dry-run=[yes|no]` to global parameter level, which requires to put them in front of the command ([`0369904`](https://github.com/cognitedata/inso-bootstrap-cli/commit/0369904f65198a61f6d2e7dc51e16e8706a61750))

* bumped version and changelog comment ([`1b16282`](https://github.com/cognitedata/inso-bootstrap-cli/commit/1b16282d950d337285154559505f2ad57166ce2a))

* moved dry-run and debug as global click-parameters ([`00c5f23`](https://github.com/cognitedata/inso-bootstrap-cli/commit/00c5f23cc84577965a0c0d4ed953325ca2680e4f))

* refactor dry_run flag ([`ee4cada`](https://github.com/cognitedata/inso-bootstrap-cli/commit/ee4cada670d696927991cff1114ae6e259aa7910))

* Merge branch &#39;main&#39; into dry-run-v0.1 ([`c2346ed`](https://github.com/cognitedata/inso-bootstrap-cli/commit/c2346edd51ca31969eb07a525b508e79332b738a))

* refactored and config ([`f90da41`](https://github.com/cognitedata/inso-bootstrap-cli/commit/f90da41c3ef4e7ce57863a3b1824da4b0208a98b))

* Added draft of Bootstrap CLI concept section with mermaid diagrams ([`4c85f8f`](https://github.com/cognitedata/inso-bootstrap-cli/commit/4c85f8f83cfb6508723f909b9b7d5f164ac30581))


## v1.4.0 (2022-04-04)

### Unknown

* Merge pull request #16 from cognitedata/limit-owner-datasets-and-rawdb-capabilities

restricted that datasets (not changed raw!)
- cannot be created or updated by owners
- only root is allowed to do so

starting test cases
- no real pytests (yet) ([`3784b70`](https://github.com/cognitedata/inso-bootstrap-cli/commit/3784b702fccd0ac49699c307cf22ec3eaea951fc))

* first start of test-cases
- not yet a pytest ([`a815c4f`](https://github.com/cognitedata/inso-bootstrap-cli/commit/a815c4fe8671de3db4868ef3a460f5e288dc73b5))

* restricted that datasets
- cannot be created or updated by users
- only root is allowed to do so ([`1274e28`](https://github.com/cognitedata/inso-bootstrap-cli/commit/1274e28d1109cd837db5e3af11d2e77885a93337))

* added basic dry-run capabilities, fixed click-library to 8.0 do to 8.1.x capability problems ([`5b4d2dc`](https://github.com/cognitedata/inso-bootstrap-cli/commit/5b4d2dc98b221398486b46458c9cc79ae94b9f5c))


## v1.3.0 (2022-03-30)

### Unknown

* Merge pull request #12 from cognitedata/refactor-prepare-and-create_function-to-support-idempotent-calls-issue#11

Refactor `prepare` and create function to support idempotent calls #11
- changed `prepare` which now requires an explicit `--aad-source-id` parameter
- small changes to python version 3.9 and README.md
- new version is 1.3.0 ([`1054511`](https://github.com/cognitedata/inso-bootstrap-cli/commit/105451109e5de9e9c0bcb5b40429616af997b0cb))

* README change to bumb a change ([`671fa19`](https://github.com/cognitedata/inso-bootstrap-cli/commit/671fa19c8e8d3246e612a44a4669b360895523d1))

* updated prepare help text and README section ([`042d39c`](https://github.com/cognitedata/inso-bootstrap-cli/commit/042d39c7b03d0f3c01684d1278fa53a21b7afd99))

* `prepare` now has an explicit parameter for the aad-source-id ([`33f8a8d`](https://github.com/cognitedata/inso-bootstrap-cli/commit/33f8a8d1c69f5ed7633e91597049e6827b8fa9e5))

* - updated README with parameter changes
- improved help texts ([`7be3b82`](https://github.com/cognitedata/inso-bootstrap-cli/commit/7be3b82f480df1311bee3c069e6de106b691bdcc))

* manual bump version from 1.2.1. to 1.3.0 ([`622555e`](https://github.com/cognitedata/inso-bootstrap-cli/commit/622555e6cfdbc5f84853ad1e0fe73b7bea27793d))

* 1. tested and fixed bugs in `prepare`
2. added global `--dotenv-path` parameter to support multiple .env files
3. added multiple **.env files to .gitignore ([`7a67a4c`](https://github.com/cognitedata/inso-bootstrap-cli/commit/7a67a4cd5200cbdc9cb3533f797486e70cb2ce0c))

* updated poetry now to 3.9 too ([`e2fecf6`](https://github.com/cognitedata/inso-bootstrap-cli/commit/e2fecf60d9c10187f90f2fd4ce4c04f4a9aedf8c))

* applied and passing pre-commit now ([`df13b6b`](https://github.com/cognitedata/inso-bootstrap-cli/commit/df13b6bf7fdaa0c028127e70ae6dcaf06b2612ab))

* refactored create_function
to be used from prepare mode too
which avoids creating multiple cdf:prepare groups ([`c313eba`](https://github.com/cognitedata/inso-bootstrap-cli/commit/c313ebac1c1ecc20486f2e9eac83161c8b51169b))

* Merge pull request #10 from cognitedata/readme-patch-1

Update README.md ([`92944a7`](https://github.com/cognitedata/inso-bootstrap-cli/commit/92944a73c4587a2bc84d2c3a280a6f60c63ea40a))

* Update README.md

fixing and add more comments to the github-action example ([`c49ea2c`](https://github.com/cognitedata/inso-bootstrap-cli/commit/c49ea2c1a26a476dc883b8809661aa09247d41c5))


## v1.2.1 (2022-02-17)

### Unknown

* Merge pull request #9 from cognitedata/special-groups-support-GH-8

1. updates and adding `--with-special-groups` support
2. upgrade py from 3.7 to 3.9 ([`8276370`](https://github.com/cognitedata/inso-bootstrap-cli/commit/82763702a0e7c631f4c2c090ad2403ddd670a790))

* fixed comment ([`9859611`](https://github.com/cognitedata/inso-bootstrap-cli/commit/98596118ec583defdec805e5694b0f990ed1c36b))

* update to 3.9 and manually set version ([`eb44c3b`](https://github.com/cognitedata/inso-bootstrap-cli/commit/eb44c3b19852de881742669cde8affebc4ae15b8))

* adding more --help output and documentation ([`63b8e5b`](https://github.com/cognitedata/inso-bootstrap-cli/commit/63b8e5bb3fa39dbcb6b8f03015fb5a1e81520c1d))

* updated changelog ([`6c5e6d1`](https://github.com/cognitedata/inso-bootstrap-cli/commit/6c5e6d1b1d074dcecd9da200530955f096030708))

* updates and adding --with-special-groups support ([`da1c5c5`](https://github.com/cognitedata/inso-bootstrap-cli/commit/da1c5c54b16a796e4a715bffcaff5ae103b7e428))

* Update version from pyproject.toml too (#7) ([`1cfbfbd`](https://github.com/cognitedata/inso-bootstrap-cli/commit/1cfbfbd3f0c447bc7836e3627e17080b00a3b75a))

* Add delete command and update README (#6)

* Add delete command with minor changes,  bump v 1.1.0 ([`eabfa0d`](https://github.com/cognitedata/inso-bootstrap-cli/commit/eabfa0dad0c5767eff934a70a053c0680d4c97d9))


## v1.1.0 (2022-02-07)

### Unknown

* Prepare (#4)

* Added prepare method like deploy with add_command ([`f619c63`](https://github.com/cognitedata/inso-bootstrap-cli/commit/f619c632e741f0f1f89717e09869d3291f36de46))

* v0.9.1 ([`f03f295`](https://github.com/cognitedata/inso-bootstrap-cli/commit/f03f2950705c61287235a1a972899117b3e8395a))
