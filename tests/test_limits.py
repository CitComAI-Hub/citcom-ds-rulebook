import unittest

from rulebook_gen import limits
from rulebook_gen.__main__ import ROOT, generate_limits


class LimitsTest(unittest.TestCase):
    def test_class_defaults_per_path(self):
        out = generate_limits(ROOT / "offers")
        self.assertEqual(out["townhall_vlc"]["/lepus/ngsi-ld"], {"count": 60, "time_window": 60})
        self.assertEqual(out["townhall_vlc"]["/ngsi-ld"], {"count": 60, "time_window": 60})
        self.assertEqual(out["vrain_upv"]["/container-location"], {"count": 600, "time_window": 60})

    def test_offer_can_override(self):
        offer = {"name": "x", "class": "dataset-access", "path": "/p", "rate_limit": {"count": 10}}
        self.assertEqual(limits.of_offer(offer), {"count": 10, "time_window": 60})

    def test_offers_of_one_path_must_agree(self):
        a = {"name": "a", "class": "dataset-access", "path": "/p"}
        b = {"name": "b", "class": "dataset-access", "path": "/p", "rate_limit": {"count": 5}}
        with self.assertRaises(ValueError):
            limits.per_path([a, b])

    def test_invalid_values_are_rejected(self):
        with self.assertRaises(ValueError):
            limits.of_offer({"name": "x", "class": "open-data", "rate_limit": {"count": 0}})
        with self.assertRaises(ValueError):
            limits.of_offer({"name": "x", "class": "open-data", "rate_limit": {"burst": 3}})
