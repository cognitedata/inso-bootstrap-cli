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