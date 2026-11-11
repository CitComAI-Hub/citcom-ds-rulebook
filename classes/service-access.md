# service-access

Access for the buying organisation's people to a web or API service.

**Terms (rulebook §7):** the service's terms of use, in its offering. Inputs users give
the service are not reused for anything else (contractual).

| Term | Kind | How |
|---|---|---|
| Only users of the buying organisation | enforced | `vc:currentParty == buyer DID` (added by contract-management) |
| Only users the buyer allowed | enforced | `vc:role hasPart <role>` AND `vc:type hasPart ServiceCredential` |
| Only this service | enforced | `http:path isInPath <path>` |

**Published terms today:** they do not yet say that user inputs are not reused
(rulebook open decision 6).

Terms and conditions published with each offer: [`service-access.terms.md`](service-access.terms.md),
filled with the `[provider.terms]` / `[offer.terms]` values of `offers/*.toml`.

Parameters: `path`, `credential`, `role`.
