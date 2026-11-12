# open-data

**For:** datasets the provider already publishes as open data (rulebook R6.2, R6.4).

**What you get:** read access, through the data space, to one dataset, for your
organisation's software. Acquiring it is free.

**What you must do:** respect the licence of the source (for example, CC BY 4.0: say
who the provider is). The data space adds no usage restrictions. You only accept the
service terms: your organisation identifies itself as a participant, and the access is
read only.

The full terms published with each offering are generated from
[`open-data.terms.md`](open-data.terms.md).

## What the software enforces

| Term | Kind |
|---|---|
| Only participants that acquired the offering | enforced |
| Only software of that organisation (machine access) | enforced |
| Only this dataset | enforced |
| Read only | enforced |
| Fair use: 60 requests per minute per organisation (R7.5) | enforced |
| Attribute the source | contractual |

### Technical detail

| Term | How |
|---|---|
| Only the buying organisation | `vc:currentParty == buyer DID` (added by contract-management on purchase) |
| Only machine access | `vc:type hasPart MachineCredential` |
| Only this dataset | `http:path isInPath <path>` AND `ngsi-ld:entityType eq <type>`; the connector must block what the policy cannot see ([implementation profiles](../docs/implementation-profiles.md)) |
| Read only | `odrl:read` (GET only) and GET-only gateway routes |
| Fair use | gateway request limit on the offering's route, counted per credential issuer; HTTP 429 over the limit |

Same enforcement as [dataset-access](dataset-access.md). The difference is legal: no
"within CitCom" restriction and no deletion duty.

Parameters in `offers/`: `path`, `entity_type`, `credential`, `role`.
