"""What each policy class must allow and deny at the gateway, as OPA inputs.

Every case is (name, expected, request). `expected` is "allow", "deny" or "gap":
a gap is a request the class should deny but OPA allows, because odrl-pap trusts
something the client sends. The gateway (APISIX, Lepus) must block it; the test
asserts that OPA allows it, so it fails, and must be revisited, the day odrl-pap
closes the gap. See AUDIT-fable.md in dataspace-on-upv (F1, F2).

`buyer`, `other_buyer` and `stranger` are DIDs: the buyer of this offer, the buyer
of another offer of the same provider, and a participant that bought nothing.
"""


def _req(method, path, query=None, body=None, headers=None, who="buyer", cred=None, roles=None):
    return {
        "method": method,
        "path": path,
        "query": query or {},
        "body": body,
        "headers": headers or {},
        "who": who,
        "cred": cred,
        "roles": roles,
    }


def dataset_access(offer):
    p, t = offer["path"], offer["entity_type"]
    urn = f"urn:ngsi-ld:{t}:x1"
    other = "OtherType"
    body = f'{{"id":"{urn}","type":"{t}"}}'
    return [
        # what a buyer does
        ("get_entities_by_type", "allow", _req("GET", f"{p}/v1/entities", {"type": t})),
        ("get_entity_by_id", "allow", _req("GET", f"{p}/v1/entities/{urn}")),
        # read only
        ("post_entities", "deny", _req("POST", f"{p}/v1/entities", {"type": t}, body)),
        ("patch_entity", "deny", _req("PATCH", f"{p}/v1/entities/{urn}/attrs", {"type": t}, "{}")),
        ("put_entity", "deny", _req("PUT", f"{p}/v1/entities/{urn}", {}, body)),
        ("delete_entity", "deny", _req("DELETE", f"{p}/v1/entities/{urn}")),
        ("batch_delete", "deny", _req("POST", f"{p}/v1/entityOperations/delete", {"type": t}, f'["{urn}"]')),
        ("post_subscription", "deny", _req("POST", f"{p}/v1/subscriptions", {"type": t}, "{}")),
        # only the type that was bought
        ("get_other_type", "deny", _req("GET", f"{p}/v1/entities", {"type": other})),
        ("get_type_list", "deny", _req("GET", f"{p}/v1/entities", {"type": f"{t},{other}"})),
        ("get_without_type", "deny", _req("GET", f"{p}/v1/entities")),
        ("get_other_urn", "deny", _req("GET", f"{p}/v1/entities/urn:ngsi-ld:{other}:x1")),
        # only under the path that was bought
        ("get_outside_path", "deny", _req("GET", f"/other{p}/v1/entities", {"type": t})),
        ("get_path_prefix_lookalike", "deny", _req("GET", f"{p}x/v1/entities", {"type": t})),
        # only the buyer, with the right credential
        ("other_buyer", "deny", _req("GET", f"{p}/v1/entities", {"type": t}, who="other_buyer")),
        ("stranger", "deny", _req("GET", f"{p}/v1/entities", {"type": t}, who="stranger")),
        ("no_token", "deny", _req("GET", f"{p}/v1/entities", {"type": t}, who=None)),
        ("wrong_credential_type", "deny", _req("GET", f"{p}/v1/entities", {"type": t}, cred="OtherCredential")),
        ("without_role", "deny", _req("GET", f"{p}/v1/entities", {"type": t}, roles=[])),
        # F1: the type comes from the client (the URN or ?type=), not from the data
        ("F1_forged_urn", "gap", _req("GET", f"{p}/v1/entities/urn:ngsi-ld:{t}:id-of-an-{other}")),
        ("F1_attrs_with_type_query", "gap",
         _req("GET", f"{p}/v1/entities/urn:ngsi-ld:{other}:x1/attrs/a", {"type": t})),
        ("F1_types_endpoint", "gap", _req("GET", f"{p}/v1/types", {"type": t})),
        # R8.5: the collection (Lepus: scopeQ -> servicePath) is chosen by the client and
        # not checked by the policy; Lepus v1.4 serves only the mapped servicePaths
        ("F1_scopeq_other_collection", "gap",
         _req("GET", f"{p}/v1/entities", {"type": t, "scopeQ": "/internal_collection"})),
        # F2: x-stripped-path replaces the path that odrl-pap checks
        ("F2_stripped_path_header", "gap",
         _req("GET", "/other/v1/entities", {"type": t}, headers={"x-stripped-path": f"{p}/v1/entities"})),
    ]


def service_access(offer):
    p = offer["path"]
    return [
        ("get_page", "allow", _req("GET", f"{p}/")),
        ("get_api", "allow", _req("GET", f"{p}/api/items", {"q": "x"})),
        ("post_api", "allow", _req("POST", f"{p}/api/run", {}, "{}")),
        ("get_outside_path", "deny", _req("GET", "/other/api")),
        ("get_path_prefix_lookalike", "deny", _req("GET", f"{p}x/api")),
        ("other_buyer", "deny", _req("GET", f"{p}/", who="other_buyer")),
        ("stranger", "deny", _req("GET", f"{p}/", who="stranger")),
        ("no_token", "deny", _req("GET", f"{p}/", who=None)),
        ("wrong_credential_type", "deny", _req("GET", f"{p}/", cred="OtherCredential")),
        ("without_role", "deny", _req("GET", f"{p}/", roles=[])),
        ("F2_stripped_path_header", "gap", _req("GET", "/other/api", headers={"x-stripped-path": f"{p}/api"})),
    ]


CASES = {
    "open-data": dataset_access,
    "dataset-access": dataset_access,
    "service-access": service_access,
}
