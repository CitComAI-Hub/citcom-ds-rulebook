# service-access

Access for the buying organisation's people to a web or API service.

**Terms (draft):** _to be written with the rulebook._

| Term | Kind | How |
|---|---|---|
| Only users of the buying organisation | enforced | `vc:currentParty == buyer DID` (added by contract-management) |
| Only users the buyer allowed | enforced | `vc:role hasPart <role>` AND `vc:type hasPart ServiceCredential` |
| Only this service | enforced | `http:path isInPath <path>` |

Parameters: `path`, `credential`, `role`.
