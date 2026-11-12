# Revocation and trust-anchor record

How access is revoked (rulebook R4.3, R4.5) and how changes to the trust anchor are
recorded (R2.5). Sources: contract-management 3.3.12 source code, trusted-issuers-list
(TIL) 0.9.1 API, On-Boarding-Portal backend source.

## Revoking one purchase (an order)

contract-management handles every TMF622 order event:

| Order event | What contract-management does |
|---|---|
| State changes to `completed` | Grants access: TIL credentials **scoped to the order** (`replaceCredentialsByScope(buyer, orderId)`), ODRL policy in the PAP (uid rewritten per order, bound to the buyer's DID), agreement. |
| State changes to **anything else** (`cancelled`, `failed`, `held`, `inProgress`…) | Revokes: deletes the TIL credentials of that order scope (`deleteCredentialsByScope`), deletes the order's policy from the PAP, and sets the agreement to `cancelled`. |
| Order deleted | Same revocation. |

In a provider's TIL every purchase row has `scope = <order id>`. The connector's own
entries have no scope, so a revocation never touches them. The trust anchor's TIL (0.8.0,
no scopes) is not involved in purchases.

So revoking a purchase is **automatic**: setting the order to `cancelled` is enough. It
only touches that order. Other purchases by the same buyer keep their own TIL scope and
policy. The operator verified it end to end (record in its conformance evidence).

Note for TMF622: create the order **without** `state` (the create schema rejects it),
then PATCH the state.

There is no expiry: an order stays active until someone changes its state. For
time-limited access, use an `odrl:dateTime` constraint (a class with an end date) or
cancel the order.

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
   contract-management revokes each one (see above). The operator's deployment has a
   script that lists a participant's orders and cancels them.

Participants registered before the portal existed (early adopters) are not portal
registrations. Removing one means calling the TIR/TIL management API by hand, and
writing it down in [`trust-anchor-changes.md`](../trust-anchor-changes.md).

## Trust-anchor record (R2.5)

The FIWARE components alone keep almost no history:

| Path that changes the trust anchor | Record kept by the stock components |
|---|---|
| Portal: approve / deactivate / delete a registration | Current status + reason + `updatedAt`. Overwritten on every change, no admin name, and **the row is deleted** with the registration. |
| Management API | None. |

R2.5 needs who, when and why, for every path. The operator's deployment adds:

1. **Database audit log** on the trust anchor's database (used by both TIR and TIL): an
   append-only table filled by triggers on the issuer, credential and claim tables
   (time, database user, operation, old and new row). It catches every path, including
   manual API calls, needs no change to FIWARE code, and the TIL's own database user
   cannot read or change it.
2. **Portal history** (On-Boarding-Portal ≥ 1.6): a `registration_event` table
   (registration, old → new status, reason, admin username, time), written on every
   status change and kept when a registration is deleted; read with
   `GET /api/admin/registrations/:id/events` (admin token). That is the *who* and
   *why* that the database log cannot see.
3. **Manual changes** are only for early adopters or emergencies, and are written down
   in [`trust-anchor-changes.md`](../trust-anchor-changes.md) *(contractual)*.
