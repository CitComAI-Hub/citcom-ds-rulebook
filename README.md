# citcom-ds-rulebook

Rules of the CitCom data space, and the code that turns them into the access
policies and the terms and conditions published on the marketplace.

- [`rulebook/`](rulebook/README.md): the rules, written for people (draft v0.2), with
  the decisions log and the open decisions.
- [`classes/`](classes/): policy classes. `<class>.md` says what the class means and
  what is enforced; `<class>.terms.md` is the template of the terms and conditions
  every offer of that class publishes.
- [`offers/`](offers/): each provider's offers, as a class plus parameters, and the
  values that fill the terms templates.
- [`rulebook_gen/`](rulebook_gen/): the generator (Python ≥ 3.11, standard library only).
- [`tests/`](tests/): unit tests, and [`tests/opa/`](tests/opa/) runs `opa test` on the
  Rego that odrl-pap generates from every offer.
- [`docs/enforcement-capabilities.md`](docs/enforcement-capabilities.md): what odrl-pap +
  OPA can and cannot enforce, and what the tests showed.
- [`docs/revocation-and-trust-anchor.md`](docs/revocation-and-trust-anchor.md): how access
  is revoked, and the record of trust-anchor changes.
- [`trust-anchor-changes.md`](trust-anchor-changes.md): trust-anchor changes made by hand (R2.5).
- [`PLAN.md`](PLAN.md): what is done and what comes next.

## Usage

```bash
python -m rulebook_gen build [--ref REF]  # → build/<provider>/<offer>.credentials.json + <offer>.terms.md
python -m rulebook_gen check             # compare with ../dataspace-on-upv (or --ds-repo PATH)
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

`offers/` holds **only what is published** in dataspace-on-upv `main`. An offer that is
still being built (a branch, a service not deployed) is added when it is deployed:
otherwise it changes the deployed ones (the verifier lists every role of a credential
type) and the drift check fails.

## How a change reaches production

To change a class, an offer or its terms, or to add an offer:

1. Change it here, on a branch: `offers/*.toml`, `classes/`, `rulebook_gen/`. CI runs
   the unit tests and `opa test` of every offer.
2. Merge it into `main`.
3. In dataspace-on-upv, on a branch: write the new commit of this repository in
   `providers/RULEBOOK_REF` and run `make rulebook-offers`
   (`scripts/rulebook_offers.sh`). It regenerates `providers/*/mrkt-offer/*.credentials.json`
   and `*.terms.md`; the diff shows exactly what changes. Open a PR.
4. After the merge, sync the server and run, on it, `P=<provider> scripts/provider_offers.sh`
   (dry-run) and then `--update`. It patches the catalog, specs and offerings in TMForum
   and keeps their ids.
5. Existing purchases keep the policy they got when their order was completed. A new
   policy applies to new orders only.

Nobody edits the generated files in dataspace-on-upv by hand: the drift job (below)
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

[`.github/workflows/ci.yml`](.github/workflows/ci.yml), on every push and PR to `main`,
daily at 05:17 UTC and by hand:

- **policies**: unit tests, `rulebook_gen build`, `tests/opa/run.sh`.
- **drift**: `rulebook_gen check` against dataspace-on-upv `main`. dataspace-on-upv is
  private: the job clones it with the secret `DS_DEPLOY_KEY`, the private half of a
  **read-only deploy key** of dataspace-on-upv ("citcom-ds-rulebook CI (read-only)",
  created 2026-11-11). Without the secret the job only warns. To rotate it: generate a
  new ed25519 key, add its public half as a read-only deploy key of dataspace-on-upv,
  replace the secret, delete the old deploy key. To revoke: delete the deploy key.

## Tests of the generated Rego

`tests/opa/run.sh` starts a throwaway odrl-pap and postgres (Docker), loads each
provider's offers as contract-management would after one purchase each (one buyer per
offer), downloads the bundles the connector's OPA would get and runs `opa test` on each
provider. The expected decisions per class are in [`tests/opa/cases.py`](tests/opa/cases.py);
`build.py` turns them into Rego tests. `GAP_` tests assert requests that OPA **allows**
but the class should not: they are blocked (or still to be blocked) at the gateway, see
[enforcement-capabilities](docs/enforcement-capabilities.md#tested-testsopa-2026-11-11).

Versions match dataspace-on-upv. When one is upgraded there, update it here and re-run:

| Component | Where |
|---|---|
| odrl-pap (1.4.10) | `PAP_IMAGE` in `tests/opa/run.sh` |
| OPA (1.11.0, default of data-space-connector chart 10.0.0) | `OPA_IMAGE` in `tests/opa/run.sh` |
| contract-management (3.3.12) | `rulebook_gen/order.py` (re-read its `PAPAdapter`) |
