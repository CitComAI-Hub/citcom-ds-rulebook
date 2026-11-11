# dataset-access

Access for the buying organisation's machines to one *shared* (not open) NGSI-LD
entity type (rulebook §6).

**Terms (rulebook §7):** use within CitCom activities only; do not share the raw data
outside the data space; attribute the provider; delete the data on the provider's
request when the order ends. All of these are contractual.

| Term | Kind | How |
|---|---|---|
| Only the buying organisation | enforced | `vc:currentParty == buyer DID` (added by contract-management) |
| Only machine clients | enforced | `vc:type hasPart MachineCredential` |
| Only this dataset | enforced | `http:path isInPath <path>` AND `ngsi-ld:entityType eq <type>` |
| Read only | enforced | `odrl:read` (GET only) + `methods: ["GET"]` on the APISIX route |

Parameters: `path`, `entity_type`, `credential`, `role`.
