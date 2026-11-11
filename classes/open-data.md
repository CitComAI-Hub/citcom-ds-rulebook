# open-data

Access through the data space to a dataset that is already open data (rulebook §6, R6.2).

**Terms:** the licence of the source (for VLCi data, CC BY 4.0: attribute
"Ajuntament de València"). The data space adds no usage restrictions. The consumer
only accepts the service terms: identify as a participant, read only.

| Term | Kind | How |
|---|---|---|
| Only participants that acquired the offer | enforced | `vc:currentParty == buyer DID` (added by contract-management) |
| Only machine clients | enforced | `vc:type hasPart MachineCredential` |
| Only this dataset | enforced | `http:path isInPath <path>` AND `ngsi-ld:entityType eq <type>` |
| Read only | enforced | `odrl:read` (GET only) + `methods: ["GET"]` on the APISIX route |
| Attribute the source | contractual | |

Same enforcement as [dataset-access](dataset-access.md). The difference is legal: no
"within CitCom" restriction and no deletion duty.

Parameters: `path`, `entity_type`, `credential`, `role`.
