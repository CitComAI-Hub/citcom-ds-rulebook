# service-access

Access for the buying organisation's people to a web or API service.

**Terms (rulebook §7):** the service's terms of use, in its offering. Inputs users give
the service are not reused for anything else (contractual).

| Term | Kind | How |
|---|---|---|
| Only users of the buying organisation | enforced | `vc:currentParty == buyer DID` (added by contract-management) |
| Only users the buyer allowed | enforced | `vc:role hasPart <role>` AND `vc:type hasPart ServiceCredential` |
| Only this service | enforced | `http:path isInPath <path>` |

Parameters: `path`, `credential`, `role`.
