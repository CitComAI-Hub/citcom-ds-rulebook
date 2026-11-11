import unittest

from rulebook_gen.__main__ import ROOT, generate
from rulebook_gen.order import instantiate


class OrderTest(unittest.TestCase):
    def setUp(self):
        chars = generate(ROOT / "offers")[("townhall_vlc", "waste-containers")]
        self.policy = chars[1]["productSpecCharacteristicValue"][0]["value"][0]

    def test_binds_the_buyer_and_keeps_the_offer_constraints(self):
        p = instantiate(self.policy, "did:web:buyer.example", "order-1")
        self.assertTrue(p["odrl:uid"].endswith("/policy/waste-containers-access-order-1"))
        party, original = p["odrl:permission"]["odrl:assignee"]["odrl:refinement"]["odrl:and"]
        self.assertEqual(party["odrl:leftOperand"], "vc:currentParty")
        self.assertEqual(party["odrl:rightOperand"], "did:web:buyer.example")
        self.assertEqual(original["odrl:and"][0]["odrl:leftOperand"], "vc:role")

    def test_template_is_not_modified(self):
        before = repr(self.policy)
        instantiate(self.policy, "did:web:buyer.example", "order-1")
        self.assertEqual(repr(self.policy), before)
