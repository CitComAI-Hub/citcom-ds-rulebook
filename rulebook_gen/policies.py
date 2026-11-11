"""Policy classes: each one turns an offer's parameters into the two TMForum
product-spec characteristics that contract-management applies on purchase:

- "Verifier policy" (credentialsConfiguration): what the TIL entry for the buyer
  allows (credential type + accepted role values).
- "ODRL policy" (authorizationPolicy): what odrl-pap turns into Rego for OPA.

contract-management (>= 3.3.12) rewrites the policy uid per order and ANDs a
`vc:currentParty == <buyer DID>` constraint into the assignee, so every policy
here is a template that is bound to one buyer at purchase time.
"""

ROLE_TARGET = "roles-dataspace"

CONTEXT = {
    "odrl": "http://www.w3.org/ns/odrl/2/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "vc": "https://www.w3.org/2018/credentials#",
    "http": "https://github.com/SEAMWARE/odrl-pap/http#",
}
NGSI_LD_CONTEXT = {"ngsi-ld": "https://uri.etsi.org/ngsi-ld/"}


def _string(value):
    return {"@value": value, "@type": "xsd:string"}


def _constraint(left, operator, right):
    return {
        "@type": "odrl:Constraint",
        "odrl:leftOperand": left,
        "odrl:operator": operator,
        "odrl:rightOperand": _string(right),
    }


def _all_of(constraints):
    if len(constraints) == 1:
        return constraints[0]
    return {"@type": "odrl:LogicalConstraint", "odrl:and": constraints}


def _odrl_policy(provider, offer, context, action, target_constraints):
    uid = f"https://{provider['host']}/policy/{offer['name']}-access"
    return {
        "@context": context,
        "@id": uid,
        "odrl:uid": uid,
        "@type": "odrl:Policy",
        "odrl:permission": [
            {
                "odrl:assigner": f"did:web:{provider['host']}",
                "odrl:action": action,
                "odrl:target": {
                    "@type": "odrl:AssetCollection",
                    "odrl:source": "urn:asset",
                    "odrl:refinement": _all_of(target_constraints),
                },
                "odrl:assignee": {
                    "@type": "odrl:PartyCollection",
                    "odrl:source": "urn:user",
                    "odrl:refinement": _all_of(
                        [
                            _constraint("vc:role", "odrl:hasPart", offer["role"]),
                            _constraint("vc:type", "odrl:hasPart", offer["credential"]),
                        ]
                    ),
                },
            }
        ],
    }


def dataset_access(provider, offer):
    """Read-only (GET) access to one NGSI-LD entity type under one path prefix."""
    targets = [
        _constraint("http:path", "http:isInPath", offer["path"]),
        _constraint("ngsi-ld:entityType", "odrl:eq", offer["entity_type"]),
    ]
    return _odrl_policy(provider, offer, CONTEXT | NGSI_LD_CONTEXT, "odrl:read", targets)


def service_access(provider, offer):
    """Access to a web/API service under one path prefix (any method: web apps POST)."""
    targets = [_constraint("http:path", "http:isInPath", offer["path"])]
    return _odrl_policy(provider, offer, CONTEXT, "odrl:use", targets)


CLASSES = {
    # open-data and dataset-access enforce the same; they differ in their legal terms
    # (rulebook §7): open data keeps its open licence, shared data is CitCom-only.
    "open-data": dataset_access,
    "dataset-access": dataset_access,
    "service-access": service_access,
}


def verifier_policy(credential, allowed_roles):
    return {
        "name": "Verifier policy",
        "valueType": "credentialsConfiguration",
        "productSpecCharacteristicValue": [
            {
                "isDefault": True,
                "value": [
                    {
                        "credentialsType": credential,
                        "claims": [
                            {
                                "name": "roles",
                                "path": f'$.roles[?(@.target=="{ROLE_TARGET}")].names[*]',
                                "allowedValues": allowed_roles,
                            }
                        ],
                    }
                ],
            }
        ],
    }


def characteristics(provider, offer, all_offers):
    """The <offer>.credentials.json content for one offer.

    The verifier checks that EVERY role of the presented credential (all roles with
    target roles-dataspace) is in the TIL entry's allowedValues (a subset check). A
    consumer's users hold all the roles their organisation gave them, so each entry
    must accept every role this provider grants with that credential type, or a user
    with two of them would be rejected.
    """
    build = CLASSES[offer["class"]]
    roles = sorted(
        {o["role"] for o in all_offers if o["credential"] == offer["credential"]}
    )
    return [
        verifier_policy(offer["credential"], roles),
        {
            "name": "ODRL policy",
            "valueType": "authorizationPolicy",
            "productSpecCharacteristicValue": [
                {"isDefault": True, "value": [build(provider, offer)]}
            ],
        },
    ]
