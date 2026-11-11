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
- [ ] Check whether a traffic-state buyer can write to orion-ld (`odrl:use` = any
      method). Test with a throwaway entity type and policy, never on real data.
- [ ] Datasets → `odrl:read`, and/or `methods: ["GET"]` on `/ngsi-ld/*` and
      `/lepus/ngsi-ld/*`. Update the PAP instances that already exist.
- [ ] Confirm on the live PAP (`GET /v1/policies` on the OPA sidecar) that each
      purchase carries `vc:currentParty == <buyer DID>`.

## Phase 2: frame (needs the project, not only us)
- [ ] Ask CitCom (coordinator, WP leads) whether a data-governance deliverable or
      agreement already exists. If it does, the rulebook implements it. If not, we
      write a proposal for them to approve.
- [ ] Rulebook v0.1 (draft) from the DSSC Blueprint rulebook model: participants and
      roles, onboarding, data and service categories, usage terms, liability,
      changes. Short, and every rule marked *enforced*, *audited* or *contractual*.
- [ ] Check legal constraints on our datasets: VLCi data is probably open data
      already (Open Data Directive; mobility and environment are High-Value Datasets,
      Reg. (EU) 2023/138). Restricting it needs a reason (added value: NGSI-LD,
      SLA, verified identity), or a "registered open" class.

## Phase 3: policy classes
- [ ] Define 3 to 5 classes, each with its legal text and enforced constraints.
      Candidates: `open-registered` (any member, read), `dataset-access` (buyer only,
      read), `service-access` (buyer's users, by role), `trial` (+ `odrl:dateTime`
      expiry), `restricted` (+ claim on organisation type or declared purpose
      via `ovc:leftOperand`).
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
