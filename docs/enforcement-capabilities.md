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
Confirmed on the live PAP on 2026-11-11 (VRAIN's waste-containers purchase) and by the
tests (`other_buyer`, `stranger`).

`PAPAdapter` reads `odrl:permission` as one object, while the generated policy has a
one-element list. It works because TMForum stores the spec in NGSI-LD and returns
one-element arrays as plain values (the same happens to `allowedValues`: a single role
comes back as a string). [`rulebook_gen/order.py`](../rulebook_gen/order.py) does the
same unwrapping, so the tests load the policy the PAP really gets. A policy with two
permissions would come back as a list and contract-management would reject it: keep
one permission per policy.

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

1. **Every offer used `odrl:use` (any method). CONFIRMED and FIXED.** On 2026-11-11,
   townhall-vlc's OPA was asked, with VRAIN's live purchase policy, about
   POST, PATCH, PUT, DELETE and `entityOperations/delete?type=WasteContainer` on
   `/lepus/ngsi-ld` as VRAIN, and allowed all of them. Nothing was sent to Lepus or
   Orion-LD. The batch delete passes the type check through the query string
   whatever IDs the body carries. Lepus forwards writes to VLCi's real Orion. Fix
   in dataspace-on-upv `fix/read-only-data-routes`: `methods: ["GET"]` on the
   NGSI-LD routes, which also covers the policies already in the PAP, and
   `odrl:read` in the dataset offers, so `dataset-access` generates `odrl:read`.
   Lesson: never let the gateway route expose more methods than the class allows.
2. **`clearence1` carries no meaning.** All four datasets use it. Thanks to the
   buyer binding it isn't a leak, but the rulebook should give roles a meaning
   (levels or classes) or drop them.
3. **The verifier policy lists every role of a credential type.** The verifier
   checks that every role in the credential is in the TIL entry's allowed values (a
   subset check), and a consumer's users hold all their roles. TIL entries themselves
   are per order (scoped), see [revocation-and-trust-anchor](revocation-and-trust-anchor.md).
   The generator derives this list automatically.

## Tested (tests/opa, 2026-11-11)

What the generated Rego decides, per class, with odrl-pap 1.4.10 and OPA 1.11.0:

- **dataset-access / open-data**: GET by type (`?type=T`) or by id
  (`urn:ngsi-ld:T:…`) under the offer's path is allowed to the buyer only. Denied:
  every write (POST, PATCH, PUT, DELETE, batch delete, subscriptions), another
  type, a type list (`?type=T,U`), no type, another path or a look-alike prefix
  (`/lepus/ngsi-ldx`), another buyer of the same provider, a participant that bought
  nothing, no token, another credential type, no role.
- **service-access**: any method under the path, buyer only; same denials for
  path, party and credential.

Gaps: OPA allows them, so the gateway has to block them (`GAP_` tests). All closed on
2026-11-11; the ones on Lepus routes only for Lepus ≥ v1.3 (never go back below it).
On the `/ngsi-ld` routes (Orion-LD, Scorpio) the id is the whole URN, so
`urn:ngsi-ld:T:…` only finds entities whose id starts with that type: this holds as long
as the provider's entity ids follow the `urn:ngsi-ld:<type>:<id>` convention (Lepus's
plain VLCi ids did not, which is why it needed the fix). A provider that loads data
with other ids must say so before offering it.

| Case | Why OPA allows it | Blocked by | Status (2026-11-11) |
|---|---|---|---|
| `GET …/entities/urn:ngsi-ld:T:<id of another type>` | the type is read from the URN the client writes | Lepus sends Orion the URN's type, replacing the client's `?type=` | closed, Lepus v1.3 (dataspace-on-upv PR #45) |
| `GET …/entities/<other urn>/attrs/a?type=T` | last path segment has no type → falls back to `?type=` | Lepus forwards the `?type=` the policy checked, Orion enforces it | closed, Lepus v1.3 (PR #45) |
| `GET …/types?type=T` | same fallback | data routes only serve `/v1/entities{,/*}` | closed, dataspace-on-upv PR #42 |
| header `x-stripped-path: <bought path>` on another path | `http:path` prefers that header | APISIX `proxy-rewrite` removes it (and the tenant headers) | closed, dataspace-on-upv PR #39, #40 |

The OPA-level tests keep asserting `allow` for these cases: OPA still allows them,
whatever the gateway does. They fail, and must be revisited, if odrl-pap changes.
