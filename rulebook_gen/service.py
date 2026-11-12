"""The rulebook as an HTTP service, for the marketplace's offer wizard.

The marketplace never writes policies or terms itself: it asks this service, which
runs the same generator as `rulebook_gen build`, at the rulebook commit the image was
built from. Internal service (no authentication): only the marketplace reaches it.

    GET  /health    → {"status": "ok"}
    GET  /classes   → the classes an offer can use, and the fields each one needs
    POST /generate  → characteristics, terms and request limit of one offer
    POST /validate  → the marketplace audit, on the specs and offerings given
    POST /check     → one spec (and its offering) about to be written, for the proxy

POST /generate body:
    {"class": "dataset-access",
     "provider": {"host": "acme.example.org", "terms": {"provider_name": "...", ...}},
     "offer": {"name": "bike-stations", "path": "/ngsi-ld", "entity_type": "...",
               "role": "...", "terms": {...}},
     "provider_offers": [{"credential": "ServiceCredential", "role": "x_user"}, ...],
     "provider_specifications": [<the provider's product specifications, as stored>]}
The verifier policy lists every role the provider grants with the same credential
type (see policies.characteristics), so the service needs the provider's other offers:
as `provider_offers`, or as its stored `provider_specifications`, from which it reads
them. With the specifications, the answer also lists in `sibling_updates` the earlier
specifications whose verifier policy must change because this offer adds a role.
"""

import json
import os
import pathlib
import re
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import limits, marketplace, terms
from .policies import CLASSES, characteristics, verifier_policy

MAX_BODY = 512 * 1024
MAX_TERM = 4000

# What the wizard asks for each class. Datasets share one role for software access
# and services get one role each (rulebook R3.4), so the role is fixed or derived.
CLASS_INFO = {
    "open-data": {
        "title": "Open data",
        "for": "A dataset that the provider already publishes as open data (rulebook R6.2, R6.4).",
        "credential": "MachineCredential",
        "role": "clearence1",
        "fields": ["name", "path", "entity_type"],
    },
    "dataset-access": {
        "title": "Shared data",
        "for": "A dataset that is not public, but not personal and not confidential (rulebook R6.1, R6.4).",
        "credential": "MachineCredential",
        "role": "clearence1",
        "fields": ["name", "path", "entity_type"],
    },
    "service-access": {
        "title": "Service",
        "for": "A web application or API offered through the data space.",
        "credential": "ServiceCredential",
        "role": None,
        "fields": ["name", "path", "role"],
    },
}

FIELDS = {
    "name": ("Short name of the offer: lowercase letters, digits and hyphens", re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")),
    "path": ("Path prefix of its route in the provider's gateway, e.g. /ngsi-ld or /route-planner", re.compile(r"^/(?!.*\.\.)[A-Za-z0-9._~/-]{0,200}$")),
    "entity_type": ("NGSI-LD entity type, a Smart Data Model where one exists", re.compile(r"^[A-Za-z][A-Za-z0-9]{0,99}$")),
    "role": ("Role the buyer gives to the people who use the service, e.g. route_planner_user", re.compile(r"^[a-z][a-z0-9_]{0,62}$")),
}
# The gaps of the terms templates, as the wizard asks for them. "provider" values
# are the same for every offer of a provider (the wizard remembers them); "offer"
# values describe one offer. Optional ones are appended to a sentence.
TERMS_FIELDS = {
    "provider_name": ("provider", False, "Your organisation's name, as it appears in the terms", "Ajuntament de València"),
    "governing_law": ("provider", False, "The law that governs the terms", "Spanish law"),
    "courts": ("provider", False, "The courts for any dispute", "the courts of the city of Valencia"),
    "data_protection_law": ("provider", False, "The data protection law you apply", "the GDPR and Spanish Organic Law 3/2018"),
    "load_targets": ("provider", False, "What heavy use must not degrade", "the Service or the VLCi platform"),
    "origin": ("offer", False, "Where the data comes from and how to cite it", 'The data comes from the city sensors. Cite: "Source: ACME (platform X)".'),
    "quality": ("offer", False, "What users can expect of the data or results", 'The data may contain errors or gaps. It is provided "as is".'),
    "source_publisher": ("offer", False, "Who publishes the open data", "the Ajuntament de València"),
    "licence": ("offer", False, "The open licence of the source", "CC BY 4.0"),
    "licence_url": ("offer", False, "Link to that licence", "https://creativecommons.org/licenses/by/4.0/"),
    "source_url": ("offer", False, "Link to the public source dataset", "https://opendata.example.org/dataset/traffic"),
    "service_name": ("offer", False, "The service, as named in the terms", "the Route Planner"),
    "results": ("offer", False, "What the service produces", "routes"),
    "load_note": ("offer", True, "Note on fair use, after 'degrades the Service'", "(optimisations run one at a time)"),
    "availability_note": ("offer", True, "Extra sentence on availability", "Jobs in progress are lost if the Service restarts."),
    "data_protection_note": ("offer", True, "Extra sentence on data protection", "The names given to the layouts are visible to the other users."),
}

HOST = re.compile(r"^(?=.{1,253}$)[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$")


CLAUSE = re.compile(r"\n\s*\n|\*\*\d+\.")


class InvalidRequest(ValueError):
    pass


def rulebook_ref():
    if os.environ.get("RULEBOOK_REF"):
        return os.environ["RULEBOOK_REF"]
    baked = pathlib.Path(__file__).with_name("REF")
    if baked.exists():
        return baked.read_text().strip()
    try:
        return subprocess.run(
            ["git", "-C", str(terms.CLASSES_DIR.parent), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def classes():
    out = []
    for cls, info in CLASS_INFO.items():
        out.append({
            "id": cls,
            "title": info["title"],
            "for": info["for"],
            "credential": info["credential"],
            "role": info["role"],
            "fields": [{"name": f, "description": FIELDS[f][0]} for f in info["fields"]],
            "terms_fields": [
                {"name": f, "scope": TERMS_FIELDS[f][0], "optional": TERMS_FIELDS[f][1],
                 "description": TERMS_FIELDS[f][2], "example": TERMS_FIELDS[f][3]}
                for f in sorted(terms.template(cls).get_identifiers())
            ],
            "rate_limit": limits.DEFAULTS[cls],
            "url": f"{terms.REPO_URL}/blob/{rulebook_ref()}/classes/{cls}.md",
        })
    return out


def _terms_values(values, where):
    if values is None:
        return {}
    if not isinstance(values, dict):
        raise InvalidRequest(f"{where} must be an object")
    for key, value in values.items():
        if not isinstance(value, str) or len(value) > MAX_TERM:
            raise InvalidRequest(f"{where}.{key} must be a string of at most {MAX_TERM} characters")
        if CLAUSE.search(value):
            # the audit would reject it: a value cannot add a paragraph or a clause
            raise InvalidRequest(f"{where}.{key} cannot contain a blank line or a clause heading (**N.)")
    return values


def generate(request):
    if not isinstance(request, dict):
        raise InvalidRequest("the body must be a JSON object")
    cls = request.get("class")
    if cls not in CLASSES:
        raise InvalidRequest(f"unknown class {cls!r}; see GET /classes")
    info = CLASS_INFO[cls]
    provider_in = request.get("provider") or {}
    offer_in = request.get("offer") or {}
    host = provider_in.get("host")
    if not isinstance(host, str) or not HOST.match(host):
        raise InvalidRequest("provider.host must be the provider's host name, e.g. acme.example.org")
    offer = {"class": cls, "credential": info["credential"]}
    if info["role"]:
        offer["role"] = info["role"]
    for field in info["fields"]:
        value = offer_in.get(field)
        if not isinstance(value, str) or not FIELDS[field][1].match(value):
            raise InvalidRequest(f"offer.{field}: {FIELDS[field][0]}")
        offer[field] = value
    provider = {"id": host, "host": host, "terms": _terms_values(provider_in.get("terms"), "provider.terms")}
    offer["terms"] = _terms_values(offer_in.get("terms"), "offer.terms")
    # optional notes are appended to a sentence: empty, or one space before them
    for values in (provider["terms"], offer["terms"]):
        for key, value in list(values.items()):
            if TERMS_FIELDS.get(key, (None, False))[1]:
                value = value.strip()
                values[key] = f" {value}" if value else ""
    for field in terms.template(cls).get_identifiers():
        if TERMS_FIELDS[field][1]:
            offer["terms"].setdefault(field, provider["terms"].get(field, ""))
    missing = terms.missing(provider, offer)
    if missing:
        raise InvalidRequest(f"terms need {missing} in provider.terms or offer.terms")
    specs = request.get("provider_specifications") or []
    if not isinstance(specs, list) or not all(isinstance(x, dict) for x in specs):
        raise InvalidRequest("provider_specifications must be a list of product specifications")
    updates, siblings = _sibling_updates(specs, offer)
    for other in request.get("provider_offers") or []:
        if not isinstance(other, dict) or not isinstance(other.get("credential"), str) \
                or not isinstance(other.get("role"), str) or not FIELDS["role"][1].match(other["role"]):
            raise InvalidRequest("provider_offers: [{credential, role}] of the provider's other offers")
        siblings.append({"credential": other["credential"], "role": other["role"]})
    ref = rulebook_ref()
    return {
        "characteristics": characteristics(provider, offer, siblings + [offer]),
        "terms": {
            "License": terms.text(provider, offer).strip("\n"),
            "Policy class": f"{cls} ({terms.REPO_URL}/blob/{ref}/classes/{cls}.md)",
        },
        "rate_limit": limits.of_offer(offer),
        "sibling_updates": updates,
        "rulebook": ref,
    }


def _spec_offer(spec):
    """(credential, role) of a stored spec generated from a class, or None."""
    odrl = marketplace._characteristic(spec, "ODRL policy")
    if odrl is None:
        return None
    try:
        policy = marketplace.canon(odrl["productSpecCharacteristicValue"])["value"]
        permission = marketplace.canon(policy["odrl:permission"])
        assignee = marketplace._constraints(permission["odrl:assignee"]["odrl:refinement"])
    except (KeyError, TypeError, AttributeError):
        return None
    if not isinstance(assignee.get("vc:type"), str) or not isinstance(assignee.get("vc:role"), str):
        return None
    return {"credential": assignee["vc:type"], "role": assignee["vc:role"]}


def _sibling_updates(specs, offer):
    """Specs whose verifier policy must list one more role after this offer."""
    found = [(spec, _spec_offer(spec)) for spec in specs]
    found = [(spec, o) for spec, o in found if o and o["credential"] == offer["credential"]]
    roles = sorted({o["role"] for _, o in found} | {offer["role"]})
    expected = marketplace.canon(verifier_policy(offer["credential"], roles))
    updates = []
    for spec, _ in found:
        current = marketplace._characteristic(spec, "Verifier policy")
        keep = {k: (current or {}).get(k) for k in ("name", "valueType", "productSpecCharacteristicValue")}
        if marketplace.canon(keep) != expected:
            updates.append({"id": spec.get("id"), "characteristic": verifier_policy(offer["credential"], roles)})
    return updates, [o for _, o in found]


def check(request):
    """Is this spec (and offering) exactly what a class generates for this provider?

    The marketplace proxy calls it before writing. Body:
        {"host": <the provider's host, from its DID>,
         "specification": <the spec as it will be stored>,
         "offering": <the offering as it will be stored, optional>,
         "provider_specifications": [<the provider's other specs>]}
    A spec without policy characteristics passes alone (a draft), but an offering
    always needs a spec generated from its class.
    """
    if not isinstance(request, dict) or not isinstance(request.get("specification"), dict):
        raise InvalidRequest('body: {"host", "specification", "offering"?, "provider_specifications"?}')
    host = request.get("host")
    if not isinstance(host, str) or not HOST.match(host):
        raise InvalidRequest("host must be the provider's host name")
    spec = request["specification"]
    offering = request.get("offering")
    others = [x for x in (request.get("provider_specifications") or [])
              if isinstance(x, dict) and x.get("id") != spec.get("id")]
    odrl = marketplace._characteristic(spec, "ODRL policy")
    verifier = marketplace._characteristic(spec, "Verifier policy")
    if odrl is None and verifier is None:
        if offering is None:
            return {"ok": True, "problems": [], "detail": "no policy characteristics (draft)"}
        return {"ok": False, "problems": ["an offering needs a specification generated from a rulebook class"]}
    if offering is None:
        # which class: the policy says it (an entity type means a dataset class; both
        # dataset classes generate the same policies, their terms differ)
        try:
            policy = marketplace.canon(odrl["productSpecCharacteristicValue"])["value"]
            permission = marketplace.canon(policy["odrl:permission"])
            target = marketplace._constraints(permission["odrl:target"]["odrl:refinement"])
        except (KeyError, TypeError, AttributeError):
            return {"ok": False, "problems": ["ODRL policy not in the shape the classes generate"]}
        cls = "dataset-access" if "ngsi-ld:entityType" in target else "service-access"
        offering = {"name": spec.get("name"), "productOfferingTerm": [
            {"name": "Policy class", "description": f"{cls} ({terms.REPO_URL})"}]}
        check_terms = False
    else:
        check_terms = True
    claim, reason = marketplace.read_offer(offering, spec)
    if claim is None:
        return {"ok": False, "problems": [reason]}
    problems = []
    if claim["host"] != host:
        problems.append(f"the policy is for {claim['host']}, not for this provider ({host})")
    offer = claim["offer"]
    siblings = [o for o in (_spec_offer(x) for x in others) if o] + [offer]
    try:
        expected = characteristics({"id": host, "host": host}, offer, siblings)
    except (KeyError, TypeError) as e:
        return {"ok": False, "problems": [f"cannot generate {offer['class']}: missing {e}"]}
    for c in expected:
        published = claim["verifier"] if c["name"] == "Verifier policy" else claim["odrl"]
        keep = {k: published.get(k) for k in ("name", "valueType", "productSpecCharacteristicValue")}
        if marketplace.canon(keep) != marketplace.canon(c):
            problems.append(f"{c['name']} is not what {offer['class']} generates")
    if check_terms:
        ref_id = marketplace.canon(offering.get("productSpecification") or {}).get("id")
        if spec.get("id") and ref_id != spec.get("id"):
            problems.append("the offering does not point to this specification")
        template_text, _ = marketplace._template_at(offer["class"], claim["ref"])
        license_text = marketplace._term(offering, "License")
        if license_text is None:
            problems.append("no License term")
        elif not marketplace._matches_template(template_text, license_text):
            problems.append(f"License is not the {offer['class']} terms template")
    return {"ok": not problems, "problems": problems, "class": offer["class"], "offer": offer["name"]}


def validate(request):
    if not isinstance(request, dict) or not isinstance(request.get("specifications"), list) \
            or not isinstance(request.get("offerings"), list):
        raise InvalidRequest('body: {"specifications": [...], "offerings": [...]}')
    results = marketplace.audit(request["specifications"], request["offerings"])
    return {
        "ok": all(status == "OK" for _, status, _ in results),
        "results": [{"offering": n, "status": s, "detail": d} for n, s, d in results],
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "citcom-rulebook"

    def _send(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"status": "ok", "rulebook": rulebook_ref()})
        if self.path == "/classes":
            return self._send(200, classes())
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        routes = {"/generate": generate, "/validate": validate, "/check": check}
        if self.path not in routes:
            return self._send(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._send(400, {"error": "bad Content-Length"})
        if length <= 0 or length > MAX_BODY:
            return self._send(413 if length > MAX_BODY else 400, {"error": f"body of 1 to {MAX_BODY} bytes expected"})
        try:
            request = json.loads(self.rfile.read(length))
            return self._send(200, routes[self.path](request))
        except json.JSONDecodeError:
            return self._send(400, {"error": "the body is not JSON"})
        except (InvalidRequest, ValueError) as e:
            return self._send(400, {"error": str(e)})

    def log_message(self, fmt, *args):  # one line per request, no bodies
        print(f"{self.address_string()} {fmt % args}", flush=True)


def serve(host="0.0.0.0", port=8080):
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"rulebook service at {host}:{port}, rulebook {rulebook_ref()}", flush=True)
    server.serve_forever()
