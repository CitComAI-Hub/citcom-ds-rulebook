# dataset-access

**For:** *shared* datasets: not public, but not personal and not confidential
(rulebook R6.1, R6.4). The provider may add requirements, such as civil liability
insurance (R5.3).

**What you get:** read access, through the data space, to one dataset, for your
organisation's software. Your organisation chooses which of its software can read
it, by giving it the data space's data-access role (`clearence1`, the same for every
dataset, rulebook R3.4).

**What you must do:**
- use the data within CitCom activities only;
- not share the raw data outside the data space;
- say who the provider is;
- delete the data if the provider asks when the order ends.

The software cannot check these duties: they are contractual (R7.2).

The full terms published with each offering are generated from
[`dataset-access.terms.md`](dataset-access.terms.md). The offerings published before
this class existed do not include "within CitCom activities only" nor the deletion
duty yet (rulebook open decision 5).

## What the software enforces

| Term | Kind |
|---|---|
| Only the organisation that acquired the offering | enforced |
| Only software of that organisation (machine access) | enforced |
| Only software the organisation gave the data-access role | enforced |
| Only this dataset | enforced |
| Read only | enforced |
| Fair use: 60 requests per minute per organisation (R7.5) | enforced |
| Within CitCom, no sharing outside, attribution, deletion | contractual |

### Technical detail

| Term | How |
|---|---|
| Only the buying organisation | `vc:currentParty == buyer DID` (added by contract-management on purchase) |
| Only machine access | `vc:type hasPart MachineCredential` |
| Only software with the data-access role | `vc:role hasPart clearence1` (in the policy) and the role in the buyer's TIL entry |
| Only this dataset | `http:path isInPath <path>` AND `ngsi-ld:entityType eq <type>`; the connector must block what the policy cannot see ([implementation profiles](../docs/implementation-profiles.md)) |
| Read only | `odrl:read` (GET only) and GET-only gateway routes |
| Fair use | gateway request limit on the offering's route, counted per credential issuer; HTTP 429 over the limit |

Parameters in `offers/`: `path`, `entity_type`, `credential`, `role`.
