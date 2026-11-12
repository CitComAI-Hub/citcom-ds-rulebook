"""Generate the offers' policy characteristics from offers/<provider>.toml.

    python -m rulebook_gen build  [--out DIR] [--ref REF]
        writes DIR/<provider>/<offer>.credentials.json, <offer>.terms.md and rate-limits.json
    python -m rulebook_gen check  --ds-repo PATH  # diffs against dataspace-on-upv
    python -m rulebook_gen audit  [--marketplace URL]  # every published offer vs its class
    python -m rulebook_gen serve  [--port 8080]        # HTTP service for the marketplace
"""

import argparse
import json
import pathlib
import subprocess
import sys
import tomllib

from . import limits, marketplace, terms

from .policies import CLASSES, characteristics

ROOT = pathlib.Path(__file__).resolve().parent.parent
REQUIRED = {
    "open-data": {"name", "path", "entity_type", "credential", "role"},
    "dataset-access": {"name", "path", "entity_type", "credential", "role"},
    "service-access": {"name", "path", "credential", "role"},
}


def load_offers(offers_dir):
    for file in sorted(pathlib.Path(offers_dir).glob("*.toml")):
        data = tomllib.loads(file.read_text())
        provider = data["provider"]
        offers = data.get("offer", [])
        for offer in offers:
            cls = offer.get("class")
            if cls not in CLASSES:
                sys.exit(f"{file}: offer {offer.get('name')}: unknown class {cls!r}")
            missing = REQUIRED[cls] - offer.keys()
            if missing:
                sys.exit(f"{file}: offer {offer['name']}: missing {sorted(missing)}")
            missing = terms.missing(provider, offer)
            if missing:
                sys.exit(f"{file}: offer {offer['name']}: terms need {missing} in [provider.terms] or [offer.terms]")
        try:
            limits.per_path(offers)
        except ValueError as e:
            sys.exit(f"{file}: {e}")
        yield provider, offers


def generate(offers_dir):
    """{(provider_id, offer_name): characteristics}"""
    out = {}
    for provider, offers in load_offers(offers_dir):
        for offer in offers:
            out[(provider["id"], offer["name"])] = characteristics(provider, offer, offers)
    return out


def _normalized(value):
    """Order of allowedValues is irrelevant to the TIL."""
    if isinstance(value, dict):
        return {k: (sorted(v) if k == "allowedValues" else _normalized(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalized(v) for v in value]
    return value


def generate_terms(offers_dir, ref):
    """{(provider_id, offer_name): <offer>.terms.md content}"""
    return {
        (provider["id"], offer["name"]): terms.document(provider, offer, ref)
        for provider, offers in load_offers(offers_dir)
        for offer in offers
    }


def generate_limits(offers_dir):
    """{provider_id: {path: {count, time_window}}}"""
    return {provider["id"]: limits.per_path(offers) for provider, offers in load_offers(offers_dir)}


def _limits_json(value):
    return json.dumps(value, indent=2) + "\n"


def current_ref():
    try:
        return subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "main"


def cmd_build(args):
    out = pathlib.Path(args.out)
    for (provider, offer), chars in generate(args.offers).items():
        path = out / provider / f"{offer}.credentials.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(chars, indent=2, ensure_ascii=False) + "\n")
        print(path)
    for (provider, offer), doc in generate_terms(args.offers, args.ref or current_ref()).items():
        path = out / provider / f"{offer}.terms.md"
        path.write_text(doc)
        print(path)
    for provider, per_path in generate_limits(args.offers).items():
        path = out / provider / "rate-limits.json"
        path.write_text(_limits_json(per_path))
        print(path)


def cmd_check(args):
    ds = pathlib.Path(args.ds_repo) / "providers"
    generated = generate(args.offers)
    failures = 0
    for (provider, offer), chars in generated.items():
        current = ds / provider / "mrkt-offer" / f"{offer}.credentials.json"
        if not current.exists():
            print(f"NEW      {provider}/{offer}")
            continue
        same = _normalized(json.loads(current.read_text())) == _normalized(chars)
        print(f"{'OK' if same else 'DIFFERS':8} {provider}/{offer}")
        failures += not same
    # Terms: the published text (front matter ignored except the class; the
    # rulebook commit in it is the one pinned in dataspace-on-upv, not this one).
    for (provider, offer), doc in generate_terms(args.offers, "-").items():
        current = ds / provider / "mrkt-offer" / f"{offer}.terms.md"
        if not current.exists():
            print(f"NEW      {provider}/{offer} (terms)")
            failures += 1
            continue
        cur = current.read_text()
        same = terms.body(cur) == terms.body(doc) and f"class: {_class_of(doc)}\n" in cur
        print(f"{'OK' if same else 'DIFFERS':8} {provider}/{offer} (terms)")
        failures += not same
    # Rate limits: one file per provider, next to its APISIX routes.
    for provider, per_path in generate_limits(args.offers).items():
        current = pathlib.Path(args.ds_repo) / "providers" / provider / "connector" / "resources" / "rate-limits.json"
        if not current.exists():
            print(f"NEW      {provider} (rate limits)")
            failures += 1
            continue
        same = json.loads(current.read_text()) == per_path
        print(f"{'OK' if same else 'DIFFERS':8} {provider} (rate limits)")
        failures += not same
    for current in sorted(ds.glob("*/mrkt-offer/*.credentials.json")):
        key = (current.parent.parent.name, current.name.removesuffix(".credentials.json"))
        if key not in generated:
            print(f"MISSING  {key[0]}/{key[1]} (in the DS repo, not in offers/)")
            failures += 1
    return 1 if failures else 0


def cmd_audit(args):
    specs = marketplace.fetch(args.marketplace, "productSpecification")
    offerings = marketplace.fetch(args.marketplace, "productOffering")
    results = marketplace.audit(specs, offerings)
    for name, status, detail in results:
        print(f"{status:8} {name}: {detail}")
    print(f"{len(results)} offerings, {sum(s != 'OK' for _, s, _ in results)} failing")
    return 1 if any(s != "OK" for _, s, _ in results) else 0


def _class_of(doc):
    return doc.split("class: ", 1)[1].split("\n", 1)[0]


def main():
    parser = argparse.ArgumentParser(prog="rulebook_gen")
    parser.add_argument("--offers", default=ROOT / "offers")
    sub = parser.add_subparsers(dest="cmd", required=True)
    build = sub.add_parser("build")
    build.add_argument("--out", default=ROOT / "build")
    build.add_argument("--ref", help="rulebook commit named in the terms (default: this checkout's HEAD)")
    check = sub.add_parser("check")
    check.add_argument("--ds-repo", default=ROOT.parent / "dataspace-on-upv")
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8080)
    audit = sub.add_parser("audit")
    audit.add_argument("--marketplace", default="https://marketplace.citcom-vrain-dataspace.eu")
    args = parser.parse_args()
    if args.cmd == "serve":
        from . import service
        return service.serve(args.host, args.port) or 0
    return {"build": cmd_build, "check": cmd_check, "audit": cmd_audit}[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
