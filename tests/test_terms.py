import unittest

from rulebook_gen import terms
from rulebook_gen.__main__ import ROOT, generate_terms


class TermsTest(unittest.TestCase):
    def setUp(self):
        self.docs = generate_terms(ROOT / "offers", "abc123")

    def test_front_matter_names_class_and_rulebook_commit(self):
        doc = self.docs[("townhall_vlc", "waste-containers")]
        self.assertIn("class: dataset-access\n", doc)
        self.assertIn("/blob/abc123/classes/dataset-access.md\n", doc)
        self.assertTrue(terms.body(doc).startswith("**1. Purpose.**"))

    def test_open_data_adds_no_restriction_to_its_licence(self):
        # rulebook R6.2
        text = terms.body(self.docs[("townhall_vlc", "traffic-state")])
        self.assertIn("CC BY 4.0", text)
        self.assertNotIn("redistribute", text)
        self.assertNotIn("${", text)

    def test_every_offer_fills_its_template(self):
        for key, doc in self.docs.items():
            self.assertNotIn("${", doc, key)
            self.assertIn("**10. Governing law and jurisdiction.**", doc, key)

    def test_missing_value_is_reported(self):
        provider = {"terms": {}}
        offer = {"class": "service-access", "terms": {"service_name": "x"}}
        self.assertIn("origin", terms.missing(provider, offer))
        self.assertNotIn("service_name", terms.missing(provider, offer))
