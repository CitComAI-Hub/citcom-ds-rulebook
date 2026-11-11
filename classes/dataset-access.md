# dataset-access

Access for the buying organisation's machines to one *shared* (not open) NGSI-LD
entity type (rulebook R6.4: data from the provider's internal platform, e.g. VLCi
through Lepus). Today: waste-containers, air-quality, traffic-flow. The provider may
add requirements such as liability insurance (R5.3).

**Terms (rulebook §7):** use within CitCom activities only; do not share the raw data
outside the data space; attribute the provider; delete the data on the provider's
request when the order ends. All of these are contractual.

| Term | Kind | How |
|---|---|---|
| Only the buying organisation | enforced | `vc:currentParty == buyer DID` (added by contract-management) |
| Only machine clients | enforced | `vc:type hasPart MachineCredential` |
| Only this dataset | enforced | `http:path isInPath <path>` AND `ngsi-ld:entityType eq <type>` |
| Read only | enforced | `odrl:read` (GET only) + `methods: ["GET"]` on the APISIX route |

Terms and conditions published with each offer: [`dataset-access.terms.md`](dataset-access.terms.md),
filled with the `[provider.terms]` / `[offer.terms]` values of `offers/*.toml`.

Parameters: `path`, `entity_type`, `credential`, `role`.
