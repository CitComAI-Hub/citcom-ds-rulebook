# citcom-ds-rulebook

Rules of the CitCom data space, and the code that turns them into the access
policies deployed on the connectors.

- [`rulebook/`](rulebook/): the rules, written for people (draft).
- [`classes/`](classes/): policy classes. Each one has its terms and the
  constraints that enforce them.
- [`offers/`](offers/): each provider's offers, as a class plus parameters.
- [`rulebook_gen/`](rulebook_gen/): generates the `<offer>.credentials.json` files
  (TMForum product-spec characteristics) and the `<offer>.terms.md` terms and
  conditions (class template + offer values) used by
  [dataspace-on-upv](https://github.com/CitComAI-Hub/dataspace-on-upv) `scripts/provider_offers.sh`.
- [`docs/enforcement-capabilities.md`](docs/enforcement-capabilities.md): what
  odrl-pap + OPA can and cannot enforce.
- [`PLAN.md`](PLAN.md): what comes next.

## Usage

Python ≥ 3.11, standard library only.

```bash
python -m rulebook_gen build             # → build/<provider>/<offer>.credentials.json + .terms.md
python -m rulebook_gen check             # compare with ../dataspace-on-upv (or --ds-repo PATH)
python -m unittest discover -s tests -t .
tests/opa/run.sh                         # opa test of every offer's Rego (needs Docker)
```

`tests/opa/run.sh` starts a throwaway odrl-pap and postgres, loads each provider's
offers as contract-management would after one purchase each, and runs
`opa test` on the bundle that the connector's OPA would download. The expected
decisions per class are in [`tests/opa/cases.py`](tests/opa/cases.py).

## How a policy reaches a request

1. `provider_offers.sh` puts the generated characteristics on the TMForum product spec.
2. When an order is completed, contract-management adds the buyer to the TIL
   (verifier policy) and creates the ODRL policy in the provider's odrl-pap,
   bound to the buyer's DID.
3. odrl-pap translates it to Rego. The OPA sidecar of APISIX evaluates it on every request.
