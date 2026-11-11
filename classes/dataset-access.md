# dataset-access

Access for the buying organisation's machines to one NGSI-LD entity type.

**Terms (draft):** _to be written with the rulebook._

| Term | Kind | How |
|---|---|---|
| Only the buying organisation | enforced | `vc:currentParty == buyer DID` (added by contract-management) |
| Only machine clients | enforced | `vc:type hasPart MachineCredential` |
| Only this dataset | enforced | `http:path isInPath <path>` AND `ngsi-ld:entityType eq <type>` |
| Read only | enforced | `odrl:read` (GET only) + `methods: ["GET"]` on the APISIX route |

Parameters: `path`, `entity_type`, `credential`, `role`.
