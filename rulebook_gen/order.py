"""What contract-management 3.3.12 does to an offer's ODRL policy on purchase
(org.fiware.iam.pap.PAPAdapter), so the tests run the same policy the PAP gets.

TMForum stores the product spec in NGSI-LD, which returns one-element arrays as
plain values; PAPAdapter relies on that (it reads `odrl:permission` as an object),
so the per-order policy has a single permission object, not a list.
"""

import copy


def _unwrap(value):
    if isinstance(value, list):
        return value[0] if len(value) == 1 else [_unwrap(v) for v in value]
    if isinstance(value, dict):
        return {k: _unwrap(v) for k, v in value.items()}
    return value


def _current_party(did):
    return {"odrl:leftOperand": "vc:currentParty", "odrl:operator": "odrl:eq", "odrl:rightOperand": did}


def instantiate(policy, buyer_did, order_id):
    """The policy contract-management creates in the provider's PAP for one order."""
    p = _unwrap(copy.deepcopy(policy))
    p["odrl:uid"] = f"{p['odrl:uid']}-{order_id}"
    perm = p["odrl:permission"]
    assignee = perm.get("odrl:assignee")
    if assignee is None:
        perm["odrl:assignee"] = buyer_did
    else:
        if isinstance(assignee, str):
            original = _current_party(assignee)
        elif "@id" in assignee:
            original = _current_party(assignee["@id"] if isinstance(assignee["@id"], str) else assignee["@id"]["@id"])
        else:
            original = assignee["odrl:refinement"]
        perm["odrl:assignee"] = {
            "@type": "odrl:PartyCollection",
            "odrl:refinement": {
                "@type": "odrl:LogicalConstraint",
                "odrl:and": [_current_party(buyer_did), original],
            },
        }
    return p
