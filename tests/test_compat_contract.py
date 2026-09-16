from pathlib import Path
import hashlib,json,unittest,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256((R/path).read_bytes()).hexdigest()
class ContractTests(unittest.TestCase):
    def test_cad_derived_model_has_policy_interface_without_external_hardware(self):
        root=E.parse(R/'models/micro_x_14.xml').getroot();contract=json.loads((R/'engineering/control_interface.json').read_text())
        self.assertEqual([a.get('joint') for a in root.find('actuator')],contract['joint_names']);self.assertEqual(len(contract['joint_names']),14)
        self.assertEqual(contract['observation_size'],3+3+14+14+14+13)
        self.assertFalse(root.findall('.//mesh'));self.assertFalse(root.findall('.//include'));self.assertFalse(any('file' in e.attrib for e in root.iter()))
        self.assertEqual(len(root.findall('.//gyro')),1);self.assertEqual(root.find('.//body').get('name'),'trunk_base')
        # Joint pivots and axes in the dynamics model follow the measured design-pose layout exactly.
        rig=json.loads((R/'models/rig.json').read_text());ref=json.loads((R/'engineering/functional_layout.json').read_text())['joints']
        for b in rig['bodies']:
            if b['joint'] in ref:
                self.assertTrue(all(abs(a-c*.001)<1e-6 for a,c in zip(b['pivot_m'],ref[b['joint']]['pivot'])),b['joint']+' pivot')
                self.assertTrue(all(abs(a-c)<1e-6 for a,c in zip(b['axis'],ref[b['joint']]['axis'])),b['joint']+' axis')
        self.assertGreater(contract['model_mass_kg'],.6);self.assertLess(contract['model_mass_kg'],1.2)
    def test_joint_limits_are_the_measured_travel(self):
        contract=json.loads((R/'engineering/control_interface.json').read_text())
        travel=json.loads((R/'engineering/joint_travel.json').read_text())['joints']
        for name in contract['joint_names']:
            self.assertEqual(contract['joint_ranges_rad'][name],[travel[name]['min_rad'],travel[name]['max_rad']],name)
            self.assertLessEqual(abs(travel[name]['min_rad']),abs(travel[name]['catalogue_rad'][0])+1e-9,name)
    def test_evaluation_is_current_and_does_not_hide_failures(self):
        data=json.loads((R/'artifacts/compat_evaluation.json').read_text())
        self.assertEqual(data['model_sha256'],sha('models/micro_x_14.xml'))
        self.assertEqual(data['all_trials_upright'],all(r['first_fall_s'] is None for r in data['results']))
        self.assertFalse(data['complete_compatibility_verified']);self.assertFalse(data['physical_verified'])
        self.assertIn('tracking_gate_passed',data)
    def test_actor_import_training_export_evidence(self):
        data=json.loads((R/'artifacts/compat_training.json').read_text());self.assertLess(data['initial_actor_max_error'],1e-5);self.assertLess(data['export_max_error'],1e-5)
        self.assertTrue(data['actor_weights_changed']);self.assertFalse(data['upstream_training_recipe_parity'])
        self.assertEqual(data['source_sha256'],json.loads((R/'engineering/policy_sources.json').read_text())['alpha_walking.onnx']['sha256'])
        self.assertEqual(data['model_sha256'],sha('models/micro_x_14.xml'))
    def test_historical_primitive_study_evidence_is_bound_to_its_archived_model(self):
        archived=sha('models/archive/micro_x_14_primitive_study.xml')
        for path in ['artifacts/official_recipe_x_validation.json','artifacts/compat_heldout_evaluation.json','artifacts/trained_500_evaluation.json','artifacts/training_500.json']:
            self.assertEqual(json.loads((R/path).read_text())['model_sha256'],archived,path)
        data=json.loads((R/'artifacts/official_recipe_x_validation.json').read_text())
        self.assertEqual(data['exit_code'],0);self.assertTrue(data['finite_output']);self.assertTrue(data['actor_weights_changed']);self.assertFalse(data['learned_locomotion_accepted'])
    def test_interference_report_is_current_and_static_assembly_is_clear(self):
        inter=json.loads((R/'artifacts/interference.json').read_text());parts=json.loads((R/'artifacts/parts.json').read_text())['parts']
        for p in parts:self.assertEqual(inter['step_sha256'][p['name']],sha(p['step']))
        self.assertTrue(inter['assembly_cleared']);self.assertEqual(len(inter['motion']),15)
    def test_no_horn_plate_is_blocked_by_its_own_link(self):
        f=json.loads((R/'artifacts/fasteners.json').read_text())
        self.assertEqual(f['bolt_path_defects'],0,
            'a horn plate whose bolt paths are filled by the ribs unioned onto it cannot be assembled')
        self.assertGreater(len(f['bolt_access']),0)
    def test_every_horn_plate_survives_its_own_servo_at_stall(self):
        s=json.loads((R/'artifacts/strength.json').read_text())
        self.assertEqual(s['plates_below_target'],[])
        for name,v in s['horn_plates'].items():
            self.assertGreaterEqual(v['safety_factor'],s['target_safety_factor'],name)
        self.assertFalse(s['physical_test']);self.assertFalse(s['fea'])
    def test_harness_calibration_is_recorded_and_honest(self):
        h=json.loads((R/'artifacts/harness_check.json').read_text())
        ref=[r for r in h['best_tracking_ratio'] if 'reference' in r['model']]
        self.assertEqual(len(ref),1,'the reference robot must be measured in the same harness')
        self.assertLess(ref[0]['best_yaw_tracking'],0.9)
        self.assertIn('conclusion',h)
if __name__=='__main__':unittest.main()
