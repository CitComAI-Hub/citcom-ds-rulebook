# Plan

Goal: the CitCom data space has written rules, and every policy deployed on a
connector comes from them. Nobody hand-writes ODRL.

```
rulebook/        human-readable rules (what is allowed, who decides)   ← people
classes/         policy classes: meaning, enforcement, terms template   ← people + us
offers/*.toml    each offer = class + parameters + terms values         ← providers
rulebook_gen     offers → <offer>.credentials.json + <offer>.terms.md   ← code
tests/opa        opa test of the Rego odrl-pap generates from them      ← CI
dataspace-on-upv rulebook_offers.sh copies them (pinned in RULEBOOK_REF);
                 provider_offers.sh publishes them in TMForum; contract-management
                 instantiates the policy per buyer in odrl-pap → Rego → OPA
```

How to change something: [README](README.md#how-a-change-reaches-production).

## Phase 0: baseline (done 2026-11-11)
- [x] Inventory of what odrl-pap 1.4.10 and contract-management 3.3.12 enforce
      ([docs/enforcement-capabilities.md](docs/enforcement-capabilities.md)).
- [x] Generator that reproduces the current `*.credentials.json` exactly
      (`python -m rulebook_gen check`), so moving to it changes nothing in production.

## Phase 1: fix what is already deployed
- [x] Buyers could write (`odrl:use` = any method): confirmed on OPA on 2026-11-11,
      fixed in dataspace-on-upv PR #32 (GET-only routes + `odrl:read`) and PR #33
      (APISIX catch-all route removed), both deployed 2026-11-11. The PAP policy of the
      existing purchase was rewritten to `odrl:read` the same day.
- [x] The live PAP carries `vc:currentParty == <buyer DID>`: confirmed on 2026-11-11
      (policy `otpnkghnxu`, VRAIN's waste-containers purchase).

## Phase 2: frame (needs the project, not only us)
- [x] Asked CitCom (2026-11-11): nobody works on data-space governance, so we write the
      proposal.
- [x] Rulebook v0.1 proposal ([rulebook/](rulebook/README.md)), based on the DSSC Blueprint
      v2.0 governance and legal building blocks. Every rule is marked *enforced*,
      *audited* or *contractual*.
- [x] Legal check of our datasets on opendata.vlci.valencia.es: traffic state, traffic
      intensity and air quality are open data (CC BY 4.0) → class `open-data`.
      Container locations are open, fill levels are not → `dataset-access`.
- [x] Decisions 2026-11-11: consortium as governance authority, VRAIN as operator
      (controls the trust anchor), 30-day notice, category by source (provisional:
      public endpoint = open, Lepus = shared).
- [ ] Still open: final R6.4 with the Ajuntament; liability and the Ajuntament's
      requirements (insurance) for Lepus data. Sensitive, in progress.
- [x] Trust-anchor change record (R2.5): audit log and portal history deployed
      2026-11-11 (see phase 3).
- [ ] Adopt a version → tag `rulebook-vX.Y`.

## Phase 3: policy classes
- [x] First classes: `open-data`, `dataset-access`, `service-access` (rulebook §7).
- [ ] More classes when an offer needs them, each with its legal text and enforced constraints.
      Candidates: `trial` (+ `odrl:dateTime` expiry), `restricted` (+ claim on
      organisation type or declared purpose via `ovc:leftOperand`).
- [x] Revocation investigated (2026-11-11, docs/revocation-and-trust-anchor.md):
      automatic per order (any state other than completed) and per participant
      (portal deactivation removes it from the trust anchor).
- [x] End-to-end test (2026-11-11): order completed → access granted (read only);
      cancelled → TIL scope and PAP policy gone, OPA denies; other purchases untouched.
- [x] Script to cancel a participant's orders: dataspace-on-upv PR #36,
      `scripts/participant_orders.sh`.
- [x] Trust-anchor audit log DEPLOYED 2026-11-11 (dataspace-on-upv PR #35):
      `audit.trust_anchor_log` in tildb, triggers on the 4 TIR/TIL tables, til has
      no access. Read: `SELECT at, db_user, tbl, op, coalesce(new_row, old_row)
      FROM audit.trust_anchor_log ORDER BY id;` as postgres on postgres-0.
- [x] Offboarding script merged (PR #36): `scripts/participant_orders.sh`.
- [x] Portal registration history DEPLOYED 2026-11-11: On-Boarding-Portal 1.6
      (dataspace-on-upv PR #37). Table `registration_event` in the portal DB (who
      approved, deactivated or deleted each registration, and when); read it with
      `GET /api/admin/registrations/:id/events` (admin token).
- [x] Terms generated from the rulebook, PUBLISHED 2026-11-11 (dataspace-on-upv PR #43, `provider_offers.sh --update`): `classes/<class>.terms.md`
      + `[provider.terms]`/`[offer.terms]` → `<offer>.terms.md` (front matter: class,
      class_url, rulebook commit). Published as the "License" term + a "Policy class" term
      (R5.2). Same text as today for 5 offers; traffic-state (open-data) now CC BY 4.0
      without the redistribution ban (R6.2).
- [ ] dataset-access terms lack the class's "within CitCom only" and "delete on request
      when the order ends": waiting for the Ajuntament (decision 2026-11-11).
- [ ] service-access terms lack "user inputs are not reused" (class); container-location
      shows layout names to other users: decide the wording.
- [ ] Rate limits (APISIX) for the classes that need them, generated from the same file.

## Phase 4: make it the only path
- [x] `opa test` the generated Rego (2026-11-11, `tests/opa/run.sh`): a throwaway
      odrl-pap 1.4.10 gets every offer as contract-management sends it (one buyer per
      offer), its bundles are tested with OPA 1.11.0. 114 cases (92 townhall_vlc, 22
      vrain_upv) pass. Mutation checks: `odrl:use` in dataset-access breaks the 24
      write cases; dropping the `vc:currentParty` binding breaks the other-buyer and
      stranger cases. `GAP_` tests document what OPA allows and the gateway must block
      (F1 client-chosen type, F2 `x-stripped-path`; dataspace-on-upv AUDIT-fable.md).
      Gateway, deployed 2026-11-11: F2 closed (PR #39, #40: `x-stripped-path` and tenant
      headers removed); data routes only serve `/v1/entities{,/*}` (PR #42), which
      closes `/types?type=`. Still open: the two F1 cases under `/v1/entities/…`
      (forged URN, `/attrs/…?type=`) → Lepus v1.3.
- [x] CI (2026-11-11, `.github/workflows/ci.yml`, push/PR/daily): unit tests, build,
      `tests/opa/run.sh`. Green.
- [x] Drift job ACTIVE (2026-11-11): secret `DS_DEPLOY_KEY` = read-only deploy key
      "citcom-ds-rulebook CI (read-only)" on dataspace-on-upv. First run green: the 6
      deployed offers match. `offers/` holds only what is published in
      dataspace-on-upv main.
- [x] dataspace-on-upv takes the generated files (2026-11-11, PR #41).
      `scripts/rulebook_offers.sh` / `make rulebook-offers[-check]` builds them with
      rulebook_gen at the commit in `providers/RULEBOOK_REF` and copies them into
      `providers/*/mrkt-offer/`. Changing a policy = change here, bump RULEBOOK_REF there,
      regenerate, PR. Publishing is still `provider_offers.sh` on the server.
- [ ] Same classes for the EDC data space: the Dataspace Protocol also carries ODRL.

## Open questions
- Who approves the rulebook and how is it versioned (consortium? per city)?
  (Governance authority decided: the consortium. Versioning: still open.)
- Is "purpose" a claim we want in the credentials (Keycloak mapper) or only in the contract?
