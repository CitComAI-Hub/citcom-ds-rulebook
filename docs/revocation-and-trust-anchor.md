# Revocation and trust-anchor record

Investigation of 2026-11-11 for rulebook R4.3 (revocation) and R2.5 (operator
neutrality). Sources: contract-management 3.3.12 source code, trusted-issuers-list
0.9.1 API (the version deployed in both connectors), On-Boarding-Portal backend
source, and the live TILs of townhall-vlc and vrain (read only).

## Revoking one purchase (an order)

contract-management handles every TMF622 order event:

| Order event | What contract-management does |
|---|---|
| State changes to `completed` | Grants access: TIL credentials **scoped to the order** (`replaceCredentialsByScope(buyer, orderId)`), ODRL policy in the PAP (uid rewritten per order, bound to the buyer's DID), agreement. |
| State changes to **anything else** (`cancelled`, `failed`, `held`, `inProgress`…) | Revokes: deletes the TIL credentials of that order scope (`deleteCredentialsByScope`), deletes the order's policy from the PAP, and sets the agreement to `cancelled`. |
| Order deleted | Same revocation. |

Checked in the connectors' TIL databases (2026-11-11): every purchase row has
`scope = <order id>`, e.g. `did:web:vrain… | MachineCredential |
urn:ngsi-ld:product-order:c54e53db…` in townhall-vlc. Each connector's own entries have
no scope, so a revocation never touches them. (The trust anchor runs TIL 0.8.0, which
has no scopes, but it is not involved in purchases.)

So revoking a purchase is **already automatic**: setting the order to `cancelled`
is enough. It only touches that order. Other purchases by the same buyer keep their
own TIL scope and policy. The live TILs confirm it. In vrain's TIL, the Ajuntament has two
separate ServiceCredential entries, one per order (MIAIS and container location).

Seen before (2026-11-05): moving an order `inProgress → completed` re-ran it cleanly and
removed the first policy, which is the PAP half of this.

**Verified end to end on 2026-11-11** (order `urn:ngsi-ld:product-order:351420ee…`, left
`cancelled` as a record). VRAIN ordered townhall-vlc's traffic-state:

| Step | PAP policies | VRAIN entries in the TIL | OPA, GET TrafficState as VRAIN | POST |
|---|---|---|---|---|
| Before | `otpnkghnxu` (waste-containers) | 1 | deny | deny |
| Order `completed` | + `qncdmxluov` | 2 | **allow** | deny (`odrl:read`) |
| Order `cancelled` | `otpnkghnxu` | 1 | deny | deny |

The other purchase (waste-containers) was not touched. Note for TMF622: create the
order **without** `state` (the create schema rejects it), then PATCH the state.

Missing: there is no expiry. An order stays active until someone changes its state. For
time-limited access, use an `odrl:dateTime` constraint (class `trial`, PLAN phase 3)
or cancel the order.

## Removing a participant (offboarding)

Two layers:

1. **Trust anchor (immediate, enforced).** In the onboarding portal, moving the
   registration out of `active`, or deleting it, calls `unregister`. That removes the
   DID from the trust anchor's TIR and TIL, and, for portal-generated DIDs, deletes its
   realm. Every verifier checks the TIR, so from then on **all** of the participant's
   credentials are rejected everywhere.
2. **Purchases (cleanup).** Its orders, as a consumer, stay `completed` in TMForum, so
   the providers' TIL entries and PAP policies remain. They are useless after step 1,
   but they would come back to life if the DID were registered again. Cancel them →
   contract-management revokes each one (see above).

Participants registered before the portal existed (the early adopters) are not
portal registrations. Removing one means calling the TIR/TIL management API by hand.

## Trust-anchor record (R2.5)

What exists today:

| Path that changes the trust anchor | Record kept |
|---|---|
| Portal: approve / deactivate / delete a registration | Current status + reason + `updatedAt`. Overwritten on every change, no admin name, and **the row is deleted** with the registration. Logs say only "by admin". |
| Management API (TIL ingress, internal source ranges only, or port-forward) | None. |

That is not enough for R2.5. Proposal:

Implemented (audit log deployed 2026-11-11; offboarding script merged; portal history merged, waiting for a new portal image):
- dataspace-on-upv `feat/trust-anchor-audit`: items 1 below (`modules/trust_anchor/audit.tf`,
  `resources/audit.sql`), tested on Postgres 16.
- On-Boarding-Portal `feat/registration-history`: item 2 (`RegistrationEvent`,
  `GET /admin/registrations/:id/events`), tested on Postgres 16.
- dataspace-on-upv `feat/participant-orders-script`: `scripts/participant_orders.sh`
  for the offboarding cleanup (cancel a participant's orders).

1. **Database audit trigger** on the trust anchor's TIL database (`tildb`, used by both
   TIR and TIL). An append-only `audit_log` table, filled by a trigger on the issuer,
   credentials and claim tables (time, operation, old and new row). It catches every
   path, including manual API calls, and needs no change to FIWARE code. Deployed with
   the trust_anchor layer in dataspace-on-upv.
2. **Portal history** (On-Boarding-Portal, our repo): a `registration_event` table
   (registration, old → new status, reason, admin username, time) written on every
   status change and kept when a registration is deleted. That is the *who* and *why*
   that the trigger cannot see.
3. Rule: manual API changes are only for the early adopters or emergencies, and are
   written in this repo's `trust-anchor-changes.md` *(contractual)*.
