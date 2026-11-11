# Plan

Goal: the CitCom data space has written rules, and every policy deployed on a
connector comes from them. Nobody hand-writes ODRL.

```
rulebook/        human-readable rules (what is allowed, who decides)   ← people
classes/         a few policy classes: legal text + what is enforced    ← people + us
offers/*.toml    each offer = class + parameters                        ← providers
rulebook_gen     offers → <offer>.credentials.json (TMForum chars)      ← code
dataspace-on-upv provider_offers.sh publishes them; contract-management
                 instantiates them per buyer in odrl-pap → Rego → OPA
```

## Phase 0: baseline (done 2026-11-11)
- [x] Inventory of what odrl-pap 1.4.10 and contract-management 3.3.12 enforce
      ([docs/enforcement-capabilities.md](docs/enforcement-capabilities.md)).
- [x] Generator that reproduces the 7 current `*.credentials.json` exactly
      (`python -m rulebook_gen check`), so moving to it changes nothing in production.

## Phase 1: fix what is already deployed
- [x] Buyers could write (`odrl:use` = any method): confirmed on OPA on 2026-11-11,
      fixed in dataspace-on-upv `fix/read-only-data-routes` (GET-only routes + `odrl:read`).
      To deploy: apply the townhall_vlc and vrain_upv connector layers, then
      `P=townhall_vlc scripts/provider_offers.sh --update`.
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
- [ ] Trust-anchor change record (R2.5): see phase 3.
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
- [x] Script to cancel a participant's orders: dataspace-on-upv `feat/participant-orders-script` (PR).
- [ ] Trust-anchor record (R2.5): audit trigger (dataspace-on-upv
      `feat/trust-anchor-audit`) + registration history (On-Boarding-Portal
      `feat/registration-history`). Written and tested; PRs, then deploy.
- [ ] Link each offer to its human-readable terms (TMForum productOfferingTerm or
      a URL in the description) so a buyer sees what they agree to.
- [ ] Rate limits (APISIX) for the classes that need them, generated from the same file.

## Phase 4: make it the only path
- [ ] `opa test` the generated Rego (via odrl-pap in CI, or its rego libs + fixtures):
      for each class, requests that must pass and requests that must fail.
- [ ] CI: validate offers, regenerate, fail if dataspace-on-upv drifts.
- [ ] `provider_offers.sh` reads the generated files (copy step or pinned version).
- [ ] Same classes for the EDC data space: the Dataspace Protocol also carries ODRL.

## Open questions
- Who approves the rulebook and how is it versioned (consortium? per city)?
- Does a city's open data stay open inside the data space, or does it get value-added terms?
- Is "purpose" a claim we want in the credentials (Keycloak mapper) or only in the contract?
