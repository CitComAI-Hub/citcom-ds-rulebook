"""The marketplace audit accepts what the classes generate and rejects the rest."""

import copy
import unittest

from rulebook_gen import marketplace, terms
from rulebook_gen.__main__ import ROOT, load_offers
from rulebook_gen.order import _unwrap
from rulebook_gen.policies import characteristics

REF = "0" * 40


def published():
    """Every offer of offers/ as the marketplace would serve it: specs and offerings,
    with TMForum's unwrapping of one-element lists."""
    specs, offerings = [], []
    for provider, offers in load_offers(ROOT / "offers"):
        for offer in offers:
            spec_id = f"urn:spec:{provider['id']}:{offer['name']}"
            specs.append({"id": spec_id, "productSpecCharacteristic": _unwrap(characteristics(provider, offer, offers))})
            url = f"{terms.REPO_URL}/blob/{REF}/classes/{offer['class']}.md"
            offerings.append({
                "name": f"{provider['id']}/{offer['name']}",
                "productSpecification": {"id": spec_id},
                "productOfferingTerm": [
                    {"name": "procurement", "description": "manual"},
                    {"name": "License", "description": terms.text(provider, offer)},
                    {"name": "Policy class", "description": f"{offer['class']} ({url})"},
                ],
            })
    return specs, offerings


def _odrl(spec):
    char = next(c for c in spec["productSpecCharacteristic"] if c["name"] == "ODRL policy")
    value = char["productSpecCharacteristicValue"]
    value = value[0] if isinstance(value, list) else value
    return value["value"][0] if isinstance(value["value"], list) else value["value"]


class MarketplaceAuditTest(unittest.TestCase):
    def setUp(self):
        self.specs, self.offerings = published()

    def status(self, name):
        results = {n: (s, d) for n, s, d in marketplace.audit(self.specs, self.offerings)}
        return results[name]

    def spec(self, name):
        offering = next(o for o in self.offerings if o["name"] == name)
        return next(s for s in self.specs if s["id"] == offering["productSpecification"]["id"])

    def offering(self, name):
        return next(o for o in self.offerings if o["name"] == name)

    def test_everything_generated_passes(self):
        for name, status, detail in marketplace.audit(self.specs, self.offerings):
            self.assertEqual(status, "OK", f"{name}: {detail}")

    def test_dataset_with_odrl_use_fails(self):
        # the write-access finding of 2026-11-11
        permission = _odrl(self.spec("townhall_vlc/waste-containers"))["odrl:permission"]
        permission = permission[0] if isinstance(permission, list) else permission
        permission["odrl:action"] = "odrl:use"
        self.assertEqual(self.status("townhall_vlc/waste-containers")[0], "FAIL")

    def test_extra_constraint_fails(self):
        permission = _odrl(self.spec("vrain_upv/waste-collection"))["odrl:permission"]
        permission = permission[0] if isinstance(permission, list) else permission
        permission["odrl:target"]["odrl:refinement"] = {
            "@type": "odrl:LogicalConstraint",
            "odrl:or": [permission["odrl:target"]["odrl:refinement"], copy.deepcopy(permission["odrl:target"]["odrl:refinement"])],
        }
        self.assertEqual(self.status("vrain_upv/waste-collection")[0], "FAIL")

    def test_verifier_without_a_sibling_role_fails(self):
        verifier = next(c for c in self.spec("vrain_upv/waste-collection")["productSpecCharacteristic"] if c["name"] == "Verifier policy")
        value = verifier["productSpecCharacteristicValue"]
        value = value[0] if isinstance(value, list) else value
        claims = value["value"]["claims"] if isinstance(value["value"], dict) else value["value"][0]["claims"]
        claim = claims[0] if isinstance(claims, list) else claims
        claim["allowedValues"] = ["waste_collection_user"]
        self.assertEqual(self.status("vrain_upv/waste-collection")[0], "FAIL")

    def test_missing_policy_class_fails(self):
        offering = self.offering("townhall_vlc/air-quality")
        offering["productOfferingTerm"] = [t for t in offering["productOfferingTerm"] if t["name"] != "Policy class"]
        self.assertEqual(self.status("townhall_vlc/air-quality"), ("FAIL", "no Policy class term"))

    def test_unknown_class_fails(self):
        for term in self.offering("townhall_vlc/air-quality")["productOfferingTerm"]:
            if term["name"] == "Policy class":
                term["description"] = "my-own-class (https://example.org)"
        self.assertEqual(self.status("townhall_vlc/air-quality")[0], "FAIL")

    def test_class_swapped_for_a_laxer_one_fails(self):
        # shared data published as open data: the policies match, the licence does not
        for term in self.offering("townhall_vlc/air-quality")["productOfferingTerm"]:
            if term["name"] == "Policy class":
                term["description"] = term["description"].replace("dataset-access", "open-data")
        self.assertEqual(self.status("townhall_vlc/air-quality")[0], "FAIL")

    def test_edited_license_fails(self):
        for term in self.offering("vrain_upv/container-location")["productOfferingTerm"]:
            if term["name"] == "License":
                term["description"] = term["description"].replace(
                    "is not reused for any other purpose", "may be reused by the Provider"
                )
        self.assertEqual(self.status("vrain_upv/container-location")[0], "FAIL")

    def test_clause_appended_fails(self):
        # the last gap of the template must not swallow an added paragraph
        for term in self.offering("vrain_upv/waste-collection")["productOfferingTerm"]:
            if term["name"] == "License":
                term["description"] += "\n\n**11. Changes.** The Provider may change these terms at any time."
        self.assertEqual(self.status("vrain_upv/waste-collection")[0], "FAIL")

    def test_paragraph_inside_a_value_fails(self):
        for term in self.offering("townhall_vlc/traffic-flow")["productOfferingTerm"]:
            if term["name"] == "License":
                term["description"] = term["description"].replace(
                    "Spanish law.", "Spanish law.\n\nThe consumer waives every right."
                )
        self.assertEqual(self.status("townhall_vlc/traffic-flow")[0], "FAIL")

    def test_license_with_a_clause_removed_fails(self):
        for term in self.offering("townhall_vlc/traffic-state")["productOfferingTerm"]:
            if term["name"] == "License":
                term["description"] = term["description"].split("**7.")[0]
        self.assertEqual(self.status("townhall_vlc/traffic-state")[0], "FAIL")


if __name__ == "__main__":
    unittest.main()
