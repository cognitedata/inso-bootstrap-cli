## diagram rework

goals:

- document idp > groups[] --read/owner--> scopes[]
  - one idp can be conneced to multiple groups
  - group can be top/ns/node level
  - only node-level can have shared-access

- one separate diagram representing the config

questions:

- instead of detail scopes [ds,raw,raw-variants,spc] => only ref configuration short name?
  - or make it subgraphs
- does it make sense to pack multiple groups in one diagram, or stick to 1:1?

## capabilities and actions overview

- list all capabilites (acls)
  - overview all actions for READ / OWNER role-types

- chapter for all idp-groups
  - subchapter for all mapped cdf-groups
    - subchapter for all configured scopes(?) `uc:all` `uc:001:demand`
    - explict list of all created scopes (ds, raw, spc)
      - mark direct or shared-access relation(?)
