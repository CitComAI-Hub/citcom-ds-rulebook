import json
import pathlib
import unittest

from rulebook_gen.__main__ import ROOT, generate


class GeneratorTest(unittest.TestCase):
    def setUp(self):
        self.out = generate(ROOT / "offers")

    def test_verifier_lists_every_role_of_the_credential_type(self):
        verifier = self.out[("vrain_upv", "tourism")][0]
        roles = verifier["productSpecCharacteristicValue"][0]["value"][0]["claims"][0]["allowedValues"]
        self.assertEqual(roles, ["container_location_user", "tourism_user", "waste_collection_user"])

    def test_dataset_policy_constrains_path_and_type(self):
        policy = self.out[("townhall_vlc", "air-quality")][1]["productSpecCharacteristicValue"][0]["value"][0]
        target = policy["odrl:permission"][0]["odrl:target"]["odrl:refinement"]["odrl:and"]
        self.assertEqual(
            {c["odrl:leftOperand"]: c["odrl:rightOperand"]["@value"] for c in target},
            {"http:path": "/lepus/ngsi-ld", "ngsi-ld:entityType": "AirQualityObserved"},
        )

    def test_policy_ids_have_no_collisions(self):
        uids = [c[1]["productSpecCharacteristicValue"][0]["value"][0]["odrl:uid"] for c in self.out.values()]
        self.assertEqual(len(uids), len(set(uids)))

    @unittest.skipUnless((ROOT.parent / "dataspace-on-upv/providers").is_dir(), "dataspace-on-upv not checked out next to this repo")
    def test_reproduces_dataspace_on_upv(self):
        from rulebook_gen.__main__ import _normalized

        ds = ROOT.parent / "dataspace-on-upv/providers"
        for (provider, offer), chars in self.out.items():
            current = json.loads((ds / provider / "mrkt-offer" / f"{offer}.credentials.json").read_text())
            with self.subTest(offer=offer):
                self.assertEqual(_normalized(current), _normalized(chars))


if __name__ == "__main__":
    unittest.main()
