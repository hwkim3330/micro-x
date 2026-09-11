from pathlib import Path
import hashlib,json,unittest,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1]
class ContractTests(unittest.TestCase):
    def test_independent_model_has_policy_interface_without_external_hardware(self):
        root=E.parse(R/'models/micro_x_14.xml').getroot();contract=json.loads((R/'engineering/control_interface.json').read_text())
        self.assertEqual([a.get('joint') for a in root.find('actuator')],contract['joint_names']);self.assertEqual(len(contract['joint_names']),14)
        self.assertEqual(contract['observation_size'],3+3+14+14+14+13)
        self.assertFalse(root.findall('.//mesh'));self.assertFalse(root.findall('.//include'));self.assertFalse(any('file' in e.attrib for e in root.iter()))
        self.assertEqual(len(root.findall('.//gyro')),1)
    def test_evaluation_is_current_and_does_not_hide_failures(self):
        data=json.loads((R/'artifacts/compat_evaluation.json').read_text())
        self.assertEqual(data['model_sha256'],hashlib.sha256((R/'models/micro_x_14.xml').read_bytes()).hexdigest())
        self.assertEqual(data['all_trials_upright'],all(r['first_fall_s'] is None for r in data['results']))
        self.assertFalse(data['complete_compatibility_verified']);self.assertFalse(data['physical_verified'])
    def test_actor_import_training_export_evidence(self):
        data=json.loads((R/'artifacts/compat_training.json').read_text());self.assertLess(data['initial_actor_max_error'],1e-5);self.assertLess(data['export_max_error'],1e-5)
        self.assertTrue(data['actor_weights_changed']);self.assertFalse(data['upstream_training_recipe_parity'])
        self.assertEqual(data['source_sha256'],json.loads((R/'engineering/policy_sources.json').read_text())['alpha_walking.onnx']['sha256'])
        self.assertEqual(data['model_sha256'],hashlib.sha256((R/'models/micro_x_14.xml').read_bytes()).hexdigest())

    def test_official_recipe_evidence_matches_model_and_adapter(self):
        data=json.loads((R/'artifacts/official_recipe_x_validation.json').read_text())
        for key,path in [('model_sha256','models/micro_x_14.xml'),('adapter_sha256','tools/train_official_recipe.py')]:
            self.assertEqual(data[key],hashlib.sha256((R/path).read_bytes()).hexdigest())
        self.assertEqual(data['exit_code'],0)
        self.assertTrue(data['finite_output']);self.assertTrue(data['actor_weights_changed'])
        self.assertFalse(data['learned_locomotion_accepted'])
