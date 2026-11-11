"""Generate the offers' policy characteristics from offers/<provider>.toml.

    python -m rulebook_gen build  [--out DIR]   # writes DIR/<provider>/<offer>.credentials.json
    python -m rulebook_gen check  --ds-repo PATH  # diffs against dataspace-on-upv
"""

import argparse
import json
import pathlib
import sys
import tomllib

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


def cmd_build(args):
    for (provider, offer), chars in generate(args.offers).items():
        path = pathlib.Path(args.out) / provider / f"{offer}.credentials.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(chars, indent=2, ensure_ascii=False) + "\n")
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
    for current in sorted(ds.glob("*/mrkt-offer/*.credentials.json")):
        key = (current.parent.parent.name, current.name.removesuffix(".credentials.json"))
        if key not in generated:
            print(f"MISSING  {key[0]}/{key[1]} (in the DS repo, not in offers/)")
            failures += 1
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(prog="rulebook_gen")
    parser.add_argument("--offers", default=ROOT / "offers")
    sub = parser.add_subparsers(dest="cmd", required=True)
    build = sub.add_parser("build")
    build.add_argument("--out", default=ROOT / "build")
    check = sub.add_parser("check")
    check.add_argument("--ds-repo", default=ROOT.parent / "dataspace-on-upv")
    args = parser.parse_args()
    return {"build": cmd_build, "check": cmd_check}[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
