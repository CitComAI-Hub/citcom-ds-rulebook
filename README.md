# citcom-ds-rulebook

[![policies](https://github.com/CitComAI-Hub/citcom-ds-rulebook/actions/workflows/policies.yml/badge.svg?branch=main)](https://github.com/CitComAI-Hub/citcom-ds-rulebook/actions/workflows/policies.yml)
[![in sync with deployment](https://github.com/CitComAI-Hub/citcom-ds-rulebook/actions/workflows/sync.yml/badge.svg?branch=main)](https://github.com/CitComAI-Hub/citcom-ds-rulebook/actions/workflows/sync.yml)
[![marketplace offers](https://github.com/CitComAI-Hub/citcom-ds-rulebook/actions/workflows/marketplace.yml/badge.svg?branch=main)](https://github.com/CitComAI-Hub/citcom-ds-rulebook/actions/workflows/marketplace.yml)
![rulebook v0.3 draft](https://img.shields.io/badge/rulebook-v0.3%20draft-lightgrey)

Rules of the CitCom data space, and the code that turns them into the access
policies and the terms and conditions published on the marketplace.

- [`rulebook/`](rulebook/README.md): the rules, written for every participant, technical
  or not (draft v0.3, DSSC Blueprint v3.0), with the decisions log and the open decisions. No participant's
  datasets or deployments, and no technical detail.
- [`classes/`](classes/): policy classes. `<class>.md` says, in plain words, what the
  class gives and asks (every offering links to it from the marketplace), then what is
  enforced and how; `<class>.terms.md` is the template of the terms and conditions
  every offering of that class publishes.
- [`offers/`](offers/): each provider's offers, as a class plus parameters, and the
  values that fill the terms templates.
- [`rulebook_gen/`](rulebook_gen/): the generator (Python ≥ 3.11, standard library only).
- [`tests/`](tests/): unit tests, and [`tests/opa/`](tests/opa/) runs `opa test` on the
  Rego that odrl-pap generates from every offer.
- [`docs/`](docs/README.md): technical annex (enforcement capabilities, implementation
  profiles per kind of connector, revocation and trust-anchor record). Generic too: the
  evidence of a specific deployment goes in its participant's conformance evidence
  (rulebook R8.7; for the operator's deployment, `CONFORMANCE.md` in dataspace-on-upv).
- [`trust-anchor-changes.md`](trust-anchor-changes.md): trust-anchor changes made by hand (R2.5).
- [`PLAN.md`](PLAN.md): what is done and what comes next.

## Usage

```bash
python -m rulebook_gen build [--ref REF]  # → build/<provider>/<offer>.credentials.json + <offer>.terms.md
python -m rulebook_gen check             # compare with ../dataspace-on-upv (or --ds-repo PATH)
python -m rulebook_gen audit             # every offer in the marketplace vs its class (or --marketplace URL)
python -m rulebook_gen serve             # HTTP service for the marketplace (port 8080)
python -m unittest discover -s tests -t .
tests/opa/run.sh                         # opa test of every offer's Rego (needs Docker)
```

## What is generated

For every offer in `offers/*.toml`:

- **`<offer>.credentials.json`**: the two TMForum product-spec characteristics that
  contract-management applies when an order is completed: the *Verifier policy*
  (TIL entry for the buyer: credential type and accepted roles) and the *ODRL policy*
  (what odrl-pap turns into Rego). See [`rulebook_gen/policies.py`](rulebook_gen/policies.py).
- **`<offer>.terms.md`**: the terms and conditions, from `classes/<class>.terms.md`
  filled with `[provider.terms]` (overridden by the offer's `[offer.terms]`). A front
  matter names the class, a link to it and the rulebook commit
  ([`rulebook_gen/terms.py`](rulebook_gen/terms.py)). The marketplace shows the text as
  the offering's "License" term and the class as its "Policy class" term (R5.2).

And one per provider:

- **`rate-limits.json`**: requests per time window that each buying organisation can
  make to each path (R7.5): the class default, or the offer's `rate_limit`. Offers that
  share a path must share the limit ([`rulebook_gen/limits.py`](rulebook_gen/limits.py)).
  dataspace-on-upv puts it on the APISIX routes (`limit-count`, keyed by the issuer of
  the buyer's credential) and keeps it in `providers/<provider>/connector/resources/`.

`offers/` holds **only what is published** in dataspace-on-upv `main`. An offer that is
still being built (a branch, a service not deployed) is added when it is deployed:
otherwise it changes the deployed ones (the verifier lists every role of a credential
type) and the drift check fails.

## Rulebook service

The marketplace does not write policies or terms itself: its offer wizard asks the
rulebook service ([`rulebook_gen/service.py`](rulebook_gen/service.py)), which runs this
generator at the commit its image was built from.

| Endpoint | Does |
|---|---|
| `GET /classes` | The classes, what each one is for, the fields it asks (name, path, entity type or role), the terms fields, the default request limit |
| `POST /generate` | One offer's characteristics, its "License" and "Policy class" terms and its request limit. Credential and role are fixed by the class for datasets; a field outside the class is ignored; values that would add a paragraph or a clause to the terms are refused. |
| `POST /validate` | The marketplace audit (`rulebook_gen audit`) on the specifications and offerings sent |
| `GET /health` | Status and rulebook commit |

Image: `ghcr.io/citcomai-hub/citcom-ds-rulebook-service:<commit>`, built by
[`image.yml`](.github/workflows/image.yml) for every commit of `main` after the tests.
Internal service, no authentication: only the marketplace's proxy reaches it.
The verifier policy of an offer lists every role its provider grants with that
credential type, so the caller sends the provider's other offers (`provider_offers`),
and when a provider adds a role, its earlier offers must be generated again.

## How a change reaches production

To change a class, an offer or its terms, or to add an offer:

1. Change it here, on a branch: `offers/*.toml`, `classes/`, `rulebook_gen/`. CI runs
   the unit tests and `opa test` of every offer.
2. Merge it into `main`.
3. In dataspace-on-upv, on a branch: write the new commit of this repository in
   `providers/RULEBOOK_REF` and run `make rulebook-offers`
   (`scripts/rulebook_offers.sh`). It regenerates `providers/*/mrkt-offer/*.credentials.json`
   and `*.terms.md`, and `providers/*/connector/resources/rate-limits.json`; the diff shows
   exactly what changes. Open a PR.
4. After the merge, sync the server and run, on it, `P=<provider> scripts/provider_offers.sh`
   (dry-run) and then `--update`. It patches the catalog, specs and offerings in TMForum
   and keeps their ids. A change in `rate-limits.json` is applied with the provider's
   connector layer (Terraform plan + apply), not by `provider_offers.sh`.
5. Existing purchases keep the policy they got when their order was completed. A new
   policy applies to new orders only.

Nobody edits the generated files in dataspace-on-upv by hand: the sync workflow (below)
catches it.

## How a policy reaches a request

1. `provider_offers.sh` puts the characteristics on the TMForum product spec and the
   terms on the offering.
2. When an order is completed, contract-management adds the buyer to the provider's TIL
   (verifier policy, scope = order) and creates the ODRL policy in the provider's
   odrl-pap, bound to the buyer's DID (`vc:currentParty`). [`rulebook_gen/order.py`](rulebook_gen/order.py)
   reproduces that step for the tests.
3. odrl-pap translates it to Rego. The OPA sidecar of APISIX evaluates it on every request.
4. Cancelling the order removes both (see [revocation](docs/revocation-and-trust-anchor.md)).

## CI

Two workflows, each with its badge at the top of this page:

- [`policies`](.github/workflows/policies.yml), on every push and PR to `main` and by
  hand: unit tests, `rulebook_gen build`, `tests/opa/run.sh`.
- [`in sync with deployment`](.github/workflows/sync.yml), on every push and PR to
  `main`, daily at 05:17 UTC and by hand: `rulebook_gen check` against
  dataspace-on-upv `main`. Red means the deployment repository does not use what this
  repository generates (for example, a class changed here and the new commit is not
  pinned there yet). It does not look at the live marketplace: the operator compares
  the published offerings with the generated files by hand after each publication.
  dataspace-on-upv is private: the job clones it with the secret `DS_DEPLOY_KEY`, the
  private half of a **read-only deploy key** of dataspace-on-upv ("citcom-ds-rulebook
  CI (read-only)", created 2026-11-11). Without the secret the job fails, except on
  pull requests from forks (no secrets there), where it only warns. To rotate it:
  generate a new ed25519 key, add its public half as a read-only deploy key of
  dataspace-on-upv, replace the secret, delete the old deploy key. To revoke: delete
  the deploy key.

- [`marketplace offers`](.github/workflows/marketplace.yml), on every push and PR to
  `main`, daily at 05:37 UTC and by hand: `rulebook_gen audit` reads every offering of
  the marketplace's public catalogue and checks that it was generated from a class.
  It reads the class and the rulebook commit from the offering's "Policy class" term,
  reads the parameters back from its ODRL policy (provider host, offer name, path,
  entity type, role, credential), generates the characteristics again and compares
  them; the "License" must be the class's terms template at that commit, filled in.
  It covers offers of any provider, registered in `offers/` or not. Limits: the
  values a provider puts in the template's gaps (its name, the quality notes...) are
  free text, so a clause hidden in one of them passes; and only what the anonymous
  catalogue lists is checked (launched offerings).

## Tests of the generated Rego

`tests/opa/run.sh` starts a throwaway odrl-pap and postgres (Docker), loads each
provider's offers as contract-management would after one purchase each (one buyer per
offer), downloads the bundles the connector's OPA would get and runs `opa test` on each
provider. The expected decisions per class are in [`tests/opa/cases.py`](tests/opa/cases.py);
`build.py` turns them into Rego tests. `GAP_` tests assert requests that OPA **allows**
but the class should not: they are blocked (or still to be blocked) at the gateway, see
[enforcement-capabilities](docs/enforcement-capabilities.md#tested-testsopa).

Versions match dataspace-on-upv. When one is upgraded there, update it here and re-run:

| Component | Where |
|---|---|
| odrl-pap (1.4.10) | `PAP_IMAGE` in `tests/opa/run.sh` |
| OPA (1.11.0, default of data-space-connector chart 10.0.0) | `OPA_IMAGE` in `tests/opa/run.sh` |
| contract-management (3.3.12) | `rulebook_gen/order.py` (re-read its `PAPAdapter`) |
| APISIX (3.15.0), VCVerifier (6.13.0) | rate limits: the key reads the issuer from the verifier's token after `openid-connect` (rewrite phase) validated it; re-check if either changes the token or the phases |
