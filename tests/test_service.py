"""The rulebook service generates exactly what `build` generates, and refuses bad input."""

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from rulebook_gen import service, terms
from rulebook_gen.__main__ import ROOT, load_offers
from rulebook_gen.policies import characteristics
from tests.test_marketplace import published


class ServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), service.Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def call(self, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.base + path, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def test_classes(self):
        status, body = self.call("/classes")
        self.assertEqual(status, 200)
        self.assertEqual({c["id"] for c in body}, {"open-data", "dataset-access", "service-access"})
        services = next(c for c in body if c["id"] == "service-access")
        self.assertIsNone(services["role"])
        fields = {f["name"]: f for f in services["terms_fields"]}
        self.assertEqual(fields["provider_name"]["scope"], "provider")
        self.assertTrue(fields["load_note"]["optional"])
        for c in body:
            for f in c["terms_fields"]:
                self.assertTrue(f["description"] and f["example"], f)

    def test_optional_notes_can_be_left_out(self):
        values = {f: "x" for f in terms.template("service-access").get_identifiers() if not f.endswith("_note")}
        status, body = self.call("/generate", {
            "class": "service-access",
            "provider": {"host": "acme.example.org", "terms": values},
            "offer": {"name": "app", "path": "/app", "role": "app_user", "terms": {"load_note": "(one job at a time)"}},
        })
        self.assertEqual(status, 200, body)
        self.assertIn("degrades the Service (one job at a time);", body["terms"]["License"])
        self.assertIn("through the marketplace.\n", body["terms"]["License"])

    def test_generates_what_build_generates(self):
        # every offer of offers/, asked through the service, gives the same policies
        for provider, offers in load_offers(ROOT / "offers"):
            for offer in offers:
                others = [{"credential": o["credential"], "role": o["role"]} for o in offers if o is not offer]
                fields = {f: offer[f] for f in service.CLASS_INFO[offer["class"]]["fields"]}
                status, body = self.call("/generate", {
                    "class": offer["class"],
                    "provider": {"host": provider["host"], "terms": provider["terms"]},
                    "offer": fields | {"terms": offer.get("terms", {})},
                    "provider_offers": others,
                })
                self.assertEqual(status, 200, body)
                self.assertEqual(body["characteristics"], characteristics(provider, offer, offers), offer["name"])
                self.assertEqual(body["terms"]["License"], terms.text(provider, offer).strip("\n"))
                self.assertTrue(body["terms"]["Policy class"].startswith(f"{offer['class']} (https://"))

    def test_dataset_role_and_credential_are_fixed(self):
        # a caller cannot widen a dataset offer by sending another role or credential
        status, body = self.call("/generate", {
            "class": "dataset-access",
            "provider": {"host": "acme.example.org", "terms": {k: "x" for k in terms.template("dataset-access").get_identifiers()}},
            "offer": {"name": "bikes", "path": "/ngsi-ld", "entity_type": "BikeHireDockingStation",
                      "role": "admin", "credential": "LegalPersonCredential"},
        })
        self.assertEqual(status, 200, body)
        text = json.dumps(body["characteristics"])
        self.assertIn('"odrl:read"', text)
        self.assertIn("clearence1", text)
        self.assertNotIn("admin", text)
        self.assertNotIn("LegalPersonCredential", text)

    def test_bad_input_is_refused(self):
        good_terms = {k: "x" for k in terms.template("service-access").get_identifiers()}
        cases = [
            {"class": "my-class"},
            {"class": "service-access", "provider": {"host": "not a host"}, "offer": {}},
            {"class": "service-access", "provider": {"host": "acme.example.org", "terms": good_terms},
             "offer": {"name": "app", "path": "/../admin", "role": "app_user"}},
            {"class": "service-access", "provider": {"host": "acme.example.org", "terms": good_terms},
             "offer": {"name": "App!", "path": "/app", "role": "app_user"}},
            {"class": "service-access", "provider": {"host": "acme.example.org", "terms": {}},
             "offer": {"name": "app", "path": "/app", "role": "app_user"}},
            {"class": "service-access", "provider": {"host": "acme.example.org",
             "terms": good_terms | {"quality": "As is.\n\n**11. Extra.** The consumer waives every right."}},
             "offer": {"name": "app", "path": "/app", "role": "app_user"}},
        ]
        for body in cases:
            status, answer = self.call("/generate", body)
            self.assertEqual(status, 400, body)
            self.assertIn("error", answer)

    def test_new_role_updates_the_earlier_specs(self):
        # vrain_upv's two services, as stored, plus a third service with a new role
        specs, _ = published()
        vrain = [x for x in specs if x["id"].startswith("urn:spec:vrain_upv:")]
        status, body = self.call("/generate", {
            "class": "service-access",
            "provider": {"host": "vrain.citcom-vrain-dataspace.eu",
                         "terms": {k: "x" for k in terms.template("service-access").get_identifiers()}},
            "offer": {"name": "route-planner", "path": "/route-planner", "role": "route_planner_user"},
            "provider_specifications": vrain,
        })
        self.assertEqual(status, 200, body)
        allowed = ["container_location_user", "route_planner_user", "waste_collection_user"]
        self.assertIn(json.dumps(allowed), json.dumps(body["characteristics"][0]))
        self.assertEqual(sorted(u["id"] for u in body["sibling_updates"]), sorted(x["id"] for x in vrain))
        for update in body["sibling_updates"]:
            self.assertIn(json.dumps(allowed), json.dumps(update["characteristic"]))

    def test_existing_role_needs_no_update(self):
        specs, _ = published()
        vrain = [x for x in specs if x["id"].startswith("urn:spec:vrain_upv:")]
        status, body = self.call("/generate", {
            "class": "service-access",
            "provider": {"host": "vrain.citcom-vrain-dataspace.eu",
                         "terms": {k: "x" for k in terms.template("service-access").get_identifiers()}},
            "offer": {"name": "waste-collection-2", "path": "/waste-collection-2", "role": "waste_collection_user"},
            "provider_specifications": vrain,
        })
        self.assertEqual(status, 200, body)
        self.assertEqual(body["sibling_updates"], [])

    def _pair(self, name):
        specs, offerings = published()
        offering = next(o for o in offerings if o["name"] == name)
        spec = next(x for x in specs if x["id"] == offering["productSpecification"]["id"])
        provider = name.split("/")[0]
        others = [x for x in specs if x["id"].startswith(f"urn:spec:{provider}:")]
        host = {"townhall_vlc": "townhall-vlc.citcom-vrain-dataspace.eu", "vrain_upv": "vrain.citcom-vrain-dataspace.eu"}[provider]
        return host, spec, offering, others

    def test_check_accepts_generated_spec_and_offering(self):
        for name in ("townhall_vlc/waste-containers", "townhall_vlc/traffic-state", "vrain_upv/container-location"):
            host, spec, offering, others = self._pair(name)
            for body in ({"host": host, "specification": spec, "provider_specifications": others},
                         {"host": host, "specification": spec, "offering": offering, "provider_specifications": others}):
                status, answer = self.call("/check", body)
                self.assertEqual(status, 200)
                self.assertTrue(answer["ok"], (name, answer))

    def test_check_rejects_another_providers_policy(self):
        # a seller cannot publish a policy for someone else's connector
        _, spec, offering, others = self._pair("vrain_upv/waste-collection")
        status, answer = self.call("/check", {"host": "acme.example.org", "specification": spec, "offering": offering})
        self.assertFalse(answer["ok"])

    def test_check_rejects_odrl_use_on_a_dataset(self):
        host, spec, offering, others = self._pair("townhall_vlc/air-quality")
        text = json.dumps(spec).replace('"odrl:read"', '"odrl:use"')
        status, answer = self.call("/check", {"host": host, "specification": json.loads(text), "provider_specifications": others})
        self.assertFalse(answer["ok"])

    def test_check_rejects_an_offering_without_class_or_with_edited_terms(self):
        host, spec, offering, others = self._pair("vrain_upv/waste-collection")
        bare = dict(offering, productOfferingTerm=[t for t in offering["productOfferingTerm"] if t["name"] != "Policy class"])
        status, answer = self.call("/check", {"host": host, "specification": spec, "offering": bare, "provider_specifications": others})
        self.assertFalse(answer["ok"])
        edited = json.loads(json.dumps(offering).replace("is not reused for any other purpose", "may be reused"))
        status, answer = self.call("/check", {"host": host, "specification": spec, "offering": edited, "provider_specifications": others})
        self.assertFalse(answer["ok"])

    def test_check_rejects_an_offering_on_a_spec_without_policies(self):
        host, spec, offering, others = self._pair("vrain_upv/waste-collection")
        draft = {"id": spec["id"], "name": "draft"}
        status, answer = self.call("/check", {"host": host, "specification": draft})
        self.assertTrue(answer["ok"])
        status, answer = self.call("/check", {"host": host, "specification": draft, "offering": offering})
        self.assertFalse(answer["ok"])

    def test_validate_uses_the_audit(self):
        specs, offerings = published()
        status, body = self.call("/validate", {"specifications": specs, "offerings": offerings})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"], body)
        for term in offerings[0]["productOfferingTerm"]:
            if term["name"] == "License":
                term["description"] += "\n\nThe Provider may change these terms at any time."
        status, body = self.call("/validate", {"specifications": specs, "offerings": offerings})
        self.assertFalse(body["ok"])


if __name__ == "__main__":
    unittest.main()
