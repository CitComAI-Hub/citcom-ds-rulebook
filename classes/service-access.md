# service-access

**For:** services (web applications, APIs, AI models) offered through the data space.

**What you get:** access to one service for the people of your organisation that your
organisation authorises.

**What you must do:** respect the service's terms of use, published in its offering.

**What the provider must do:** not reuse, for anything else, the inputs your users give
the service (contractual, clause 8 of the terms).

The full terms published with each offering are generated from
[`service-access.terms.md`](service-access.terms.md).

## What the software enforces

| Term | Kind |
|---|---|
| Only people of the organisation that acquired the offering | enforced |
| Only the people that organisation authorised | enforced |
| Only this service | enforced |
| Fair use: 600 requests per minute per organisation (R7.5) | enforced |
| Inputs not reused | contractual |

### Technical detail

| Term | How |
|---|---|
| Only the buying organisation | `vc:currentParty == buyer DID` (added by contract-management on purchase) |
| Only authorised people | `vc:role hasPart <role>` AND `vc:type hasPart ServiceCredential` |
| Only this service | `http:path isInPath <path>` |
| Fair use | gateway request limit on the offering's route, counted per credential issuer; HTTP 429 over the limit |

Parameters in `offers/`: `path`, `credential`, `role`.
