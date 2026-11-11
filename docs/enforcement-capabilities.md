# What the FIWARE stack can enforce

Inventory made on 2026-11-11 by reading the source code of the versions deployed in
dataspace-on-upv: **odrl-pap 1.4.10** (`src/main/resources/mapping.json` and `rego/`) and
**contract-management 3.3.12** (`pap/PAPAdapter.java`). Re-check it when either one
is upgraded.

It answers one question for the rulebook: which terms can be **enforced** at
request time, and which can only be **audited** or written into the **contract**.

## Request-time enforcement (ODRL → Rego, evaluated by OPA in APISIX)

| ODRL term | Meaning in Rego | Use for |
|---|---|---|
| `odrl:read` | method == GET | read-only datasets |
| `odrl:use` | any of GET/POST/PUT/PATCH/DELETE | services (see the warning below) |
| `odrl:modify` / `odrl:delete` | PATCH / DELETE | write access |
| `ngsild:create` | POST | contributing data |
| `http:path` + `http:isInPath` | path prefix (honours `x-stripped-path`) | which API |
| `http:bodyValue` | JSON path in the request body | write access to some attributes only |
| `ngsi-ld:entityType` | type taken from the URN in the path, `?type=`, or the body | which dataset |
| `vc:type` | credential type | which kind of consumer (machine or person) |
| `vc:role` | `credentialSubject.roles[target == organization-did].names` | access level |
| `vc:currentParty` | credential **issuer** (the consumer's DID) | which organisation |
| `ovc:leftOperand` (Gaia-X profile) | any claim of the credential, by JSON path | e.g. organisation type, country, declared purpose |
| `odrl:dateTime` | current time | validity period, expiry |
| `odrl:dayOfWeek`, `odrl:hourOfDay` | current weekday or hour (UTC) | time windows |
| operators | `eq neq lt lteq gt gteq hasPart isPartOf isAllOf isAnyOf isNoneOf anyOf regex` | |
| logic | `and or xone andSequence` | |

The table also lists DOME, TMForum, DSP (`dspace:*`) and plain JSON vocabularies; we
don't use them.

### What contract-management adds on purchase

For every completed order it creates the offer's ODRL policy in the provider's PAP and:
- rewrites its uid per order, so each purchase gets its own policy instance;
- ANDs **`vc:currentParty == <buyer DID>`** into the assignee, so the policy only
  applies to credentials issued by the buyer.

A purchase therefore binds access to the buyer's organisation. A shared role
such as `clearence1` does not give access to datasets the buyer did not buy.
Still to confirm on the live PAP (plan, phase 1).

## What it cannot enforce

- **Duties and prohibitions.** odrl-pap only translates `odrl:permission`.
  `odrl:duty` and `odrl:prohibition` are ignored. Attribution, "delete after N days",
  "no redistribution" and "notify on breach" can only be contractual or audited.
- **Counting** (N requests or N downloads). OPA has no state. Rate limits go in
  APISIX (`limit-count`, `limit-req`) and live outside ODRL.
- **Purpose of use.** It can be checked only as a claim the consumer *declares* in
  its credential (`ovc:leftOperand`). Nothing verifies what the data is actually
  used for.
- **What happens after delivery.** Copies, derived data and model training are
  outside the gateway.

## Findings on the current policies

1. **Every offer uses `odrl:use` (any method).** `/ngsi-ld/*` reaches orion-ld with no
   method restriction, so a buyer of *traffic-state* may be able to POST/PATCH/DELETE
   `TrafficState` entities. The type check passes because the type comes from the
   URN in the path. `/lepus/ngsi-ld/*` depends on whether Lepus accepts writes. Needs
   to be verified without touching real data. Fix it by using `odrl:read` for
   datasets and/or `methods: ["GET"]` on the routes. Existing PAP instances keep
   `odrl:use` until they are updated, because a new policy only applies to new orders.
2. **`clearence1` carries no meaning.** All four datasets use it. Thanks to the
   buyer binding it isn't a leak, but the rulebook should give roles a meaning
   (levels or classes) or drop them.
3. **The verifier policy has to list every role of a credential type.** The TIL
   keeps one entry per (buyer, credential type), and a later purchase would
   overwrite the earlier one. The generator derives this list automatically.
