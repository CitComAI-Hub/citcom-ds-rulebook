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
        self.assertIn("provider_name", services["terms_fields"])

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
