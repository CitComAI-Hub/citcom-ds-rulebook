"""Check the offers published in a marketplace against the rulebook.

Every published offering must name its class in a "Policy class" term, and its
product specification must carry exactly the characteristics that the class
generates for the parameters the offer uses (rulebook R2.4, R5.2). The parameters are
read back from the published ODRL policy (provider host, offer name, path, entity
type, role, credential type), the characteristics are generated again and both are
compared. The "License" term must be the class's terms template, filled in.

This needs no registration of the offer in offers/: anything generated from a class
passes, anything else fails. It reads the marketplace's public catalogue only.
"""

import json
import re
import string
import subprocess
import urllib.request

from . import terms
from .policies import CLASSES, characteristics

POLICY_CLASS = re.compile(r"^\s*([a-z-]+)\s*\((\S+)\)\s*$")
UID = re.compile(r"^https://([^/]+)/policy/(.+)-access$")


def fetch(base_url, kind):
    url = f"{base_url.rstrip('/')}/catalog/{kind}?limit=1000"
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def canon(value):
    """TMForum stores the specs as NGSI-LD: one-element lists come back as plain
    values, and some plain values come back as one-element lists. Compare both sides
    in a form where a one-element list and its element are the same; the order of
    allowedValues does not matter to the verifier."""
    if isinstance(value, dict):
        return {
            k: (sorted(canon(v)) if k == "allowedValues" and isinstance(canon(v), list) else canon(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        items = [canon(v) for v in value]
        return items[0] if len(items) == 1 else items
    return value


def _list(value):
    return value if isinstance(value, list) else ([] if value is None else [value])


def _constraints(refinement):
    """{leftOperand: rightOperand value} of a constraint or an odrl:and of them."""
    refinement = canon(refinement)
    parts = _list(refinement.get("odrl:and", refinement))
    return {
        c["odrl:leftOperand"]: canon(c["odrl:rightOperand"])["@value"]
        for c in parts
        if "odrl:leftOperand" in c
    }


def _characteristic(spec, name):
    for c in _list(spec.get("productSpecCharacteristic")):
        if c.get("name") == name:
            return c
    return None


def _term(offering, name):
    for t in _list(offering.get("productOfferingTerm")):
        if t.get("name") == name:
            return t.get("description", "")
    return None


def read_offer(offering, spec):
    """The class and parameters an offering claims, or (None, reason)."""
    term = _term(offering, "Policy class")
    if term is None:
        return None, "no Policy class term"
    match = POLICY_CLASS.match(term)
    if not match or match.group(1) not in CLASSES:
        return None, f"unknown policy class {term!r}"
    cls, class_url = match.groups()
    odrl = _characteristic(spec, "ODRL policy")
    verifier = _characteristic(spec, "Verifier policy")
    if odrl is None or verifier is None:
        return None, "ODRL policy or Verifier policy characteristic missing"
    try:
        policy = canon(odrl["productSpecCharacteristicValue"])["value"]
        uid = UID.match(policy["@id"])
        permission = canon(policy["odrl:permission"])
        target = _constraints(permission["odrl:target"]["odrl:refinement"])
        assignee = _constraints(permission["odrl:assignee"]["odrl:refinement"])
    except (KeyError, TypeError):
        return None, "ODRL policy not in the shape the classes generate"
    if not uid:
        return None, f"policy id {policy.get('@id')!r} is not https://<host>/policy/<offer>-access"
    host, name = uid.groups()
    offer = {
        "class": cls,
        "name": name,
        "path": target.get("http:path"),
        "credential": assignee.get("vc:type"),
        "role": assignee.get("vc:role"),
    }
    if "ngsi-ld:entityType" in target:
        offer["entity_type"] = target["ngsi-ld:entityType"]
    ref = class_url.rsplit("/blob/", 1)[-1].split("/", 1)[0] if "/blob/" in class_url else None
    return {"host": host, "offer": offer, "ref": ref, "verifier": verifier, "odrl": odrl}, None


def _template_at(cls, ref):
    """The class's terms template at the rulebook commit the offer names; the
    current one if that commit is not in this checkout."""
    if ref:
        try:
            text = subprocess.run(
                ["git", "-C", str(terms.CLASSES_DIR.parent), "show", f"{ref}:classes/{cls}.terms.md"],
                capture_output=True, text=True, check=True,
            ).stdout
            return text, ref
        except (OSError, subprocess.CalledProcessError):
            pass
    return (terms.CLASSES_DIR / f"{cls}.terms.md").read_text(), None


def _matches_template(template_text, license_text):
    """Every fixed part of the template, in order, with anything in the ${...} gaps."""
    template_text = template_text.strip("\n")
    pattern = ""
    last = 0
    for m in string.Template.pattern.finditer(template_text):
        if m.group("named") or m.group("braced"):
            # a provider's value is free text, but it cannot open a new paragraph or
            # clause: that is how a clause would be added to the class's terms
            pattern += re.escape(template_text[last:m.start()]) + r"((?:(?!\n\s*\n|\*\*\d+\.).)*?)"
            last = m.end()
    pattern += re.escape(template_text[last:])
    return re.fullmatch(pattern, license_text.strip("\n"), re.S) is not None


def audit(specs, offerings):
    """[(offering name, status, detail)]; status is OK or FAIL."""
    by_spec = {s["id"]: s for s in specs}
    read = []
    results = []
    for offering in offerings:
        spec_id = canon(offering.get("productSpecification") or {}).get("id")
        spec = by_spec.get(spec_id)
        if spec is None:
            results.append((offering.get("name"), "FAIL", f"product specification {spec_id} not found"))
            continue
        claim, reason = read_offer(offering, spec)
        if claim is None:
            results.append((offering.get("name"), "FAIL", reason))
            continue
        read.append((offering, claim))
    # The verifier policy of an offer lists every role its provider grants with that
    # credential type, so offers are generated per provider.
    siblings = {}
    for _, claim in read:
        siblings.setdefault(claim["host"], []).append(claim["offer"])
    for offering, claim in read:
        provider = {"id": claim["host"], "host": claim["host"]}
        offer = claim["offer"]
        problems = []
        try:
            expected = characteristics(provider, offer, siblings[claim["host"]])
        except (KeyError, TypeError) as e:
            results.append((offering.get("name"), "FAIL", f"cannot generate {offer['class']}: missing {e}"))
            continue
        expected = {c["name"]: canon(c) for c in expected}
        for name, published in (("Verifier policy", claim["verifier"]), ("ODRL policy", claim["odrl"])):
            keep = {k: published.get(k) for k in ("name", "valueType", "productSpecCharacteristicValue")}
            if canon(keep) != expected[name]:
                problems.append(f"{name} differs from what {offer['class']} generates")
        template_text, ref = _template_at(offer["class"], claim["ref"])
        license_text = _term(offering, "License")
        if license_text is None:
            problems.append("no License term")
        elif not _matches_template(template_text, license_text):
            problems.append(f"License is not the {offer['class']} terms template")
        detail = f"{offer['class']}, {claim['host']}/{offer['name']}"
        if claim["ref"] and ref is None:
            detail += f", rulebook {claim['ref'][:7]} unknown here (current template used)"
        results.append((offering.get("name"), "FAIL" if problems else "OK", "; ".join(problems) or detail))
    return results
