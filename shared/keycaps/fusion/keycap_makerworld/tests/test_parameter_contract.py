import ast
import json
import pathlib
import runpy
import unittest


PROJECT_DIR = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_FILE = PROJECT_DIR / "makerworld-inputs.json"
SCRIPT_FILE = PROJECT_DIR / "keycap_makerworld.py"
PROFILE_SCRIPT_FILE = PROJECT_DIR / "print_profiles" / "build_bambu_3mf_profiles.py"
GENERATOR_SCRIPT_FILE = PROJECT_DIR.parent / "keycap_1u_choc" / "keycap_1u_choc.py"


def assigned_literal(module, variable_name):
    for node in module.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == variable_name
                for target in node.targets
            ):
                return ast.literal_eval(node.value)
    raise AssertionError("{} is not assigned in {}".format(variable_name, SCRIPT_FILE))


class ParameterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_FILE.read_text(encoding="utf-8"))
        cls.inputs = cls.contract["inputs"]
        cls.script_module = ast.parse(SCRIPT_FILE.read_text(encoding="utf-8"))
        cls.profile_script_module = ast.parse(
            PROFILE_SCRIPT_FILE.read_text(encoding="utf-8"))
        cls.generator_script_module = ast.parse(
            GENERATOR_SCRIPT_FILE.read_text(encoding="utf-8"))
        cls.generator_source = GENERATOR_SCRIPT_FILE.read_text(encoding="utf-8")
        cls.profile_script_values = runpy.run_path(
            str(PROFILE_SCRIPT_FILE), run_name="test_bambu_profile_builder")

    def test_parameter_names_are_unique(self):
        names = [item["name"] for item in self.inputs]
        self.assertEqual(len(names), len(set(names)))

    def test_defaults_are_inside_ranges(self):
        for item in self.inputs:
            with self.subTest(parameter=item["name"]):
                self.assertLessEqual(item["minimum"], item["default"])
                self.assertLessEqual(item["default"], item["maximum"])
                self.assertGreater(item["step"], 0)

    def test_expected_public_parameters_are_present(self):
        self.assertEqual(
            {item["name"] for item in self.inputs},
            {
                "skirt_h",
                "taper_h",
                "cyl_dia",
                "cyl_h",
                "dish_depth",
                "sweep",
                "wall",
                "chamfer_top",
                "chamfer_bottom",
                "chamfer_cyl",
                "chamfer_skirt",
            },
        )

    def test_dish_depth_cannot_reach_zero(self):
        dish = next(item for item in self.inputs if item["name"] == "dish_depth")
        self.assertGreater(dish["minimum"], 0)

    def test_top_sweep_is_optional_and_signed(self):
        sweep = next(item for item in self.inputs if item["name"] == "sweep")
        self.assertEqual(sweep["unit"], "deg")
        self.assertEqual(sweep["default"], 0)
        self.assertLess(sweep["minimum"], 0)
        self.assertGreater(sweep["maximum"], 0)

    def test_script_and_contract_expose_the_same_parameters(self):
        public_parameters = assigned_literal(self.script_module, "PUBLIC_PARAMETERS")
        self.assertEqual(
            set(public_parameters),
            {item["name"] for item in self.inputs},
        )

    def test_generator_defaults_match_contract(self):
        model_values = assigned_literal(self.script_module, "MODEL_VALUES")
        for item in self.inputs:
            with self.subTest(parameter=item["name"]):
                self.assertEqual(model_values[item["name"]], item["default"])

    def test_release_model_is_side_oriented(self):
        model_values = assigned_literal(self.script_module, "MODEL_VALUES")
        self.assertIs(model_values.get("orient_for_print"), True)

    def test_choc_stem_interface_is_fixed_height(self):
        self.assertEqual(
            assigned_literal(self.generator_script_module, "CHOC_STEM_TOTAL_H"),
            3.1,
        )
        self.assertEqual(
            assigned_literal(self.generator_script_module, "STEM_PROTRUDE"),
            1.4,
        )
        stem_block = self.generator_source.split("# 9. Fixed-height stems", 1)[1]
        stem_block = stem_block.split("# MakerWorld release geometry", 1)[0]
        self.assertIn("stem_total_h", stem_block)
        self.assertNotIn("ToEntityExtentDefinition", stem_block)

    def test_upper_body_uses_a_fixed_height_cavity_not_a_full_shell(self):
        self.assertIn('cavity_feature.name = "Fixed-height lower cavity"', self.generator_source)
        self.assertIn('createByString("stem_mount_h")', self.generator_source)

    def test_deep_raised_dishes_cannot_create_an_enclosed_void(self):
        self.assertIn(
            '"cyl_effective_h", "max(cyl_h; dish_depth)"',
            self.generator_source,
        )
        self.assertIn('"cyl_effective_h - dish_depth + dish_r"', self.generator_source)

    def test_raised_top_uses_a_native_join_without_an_intermediate_combine(self):
        raised_block = self.generator_source.split(
            "# 4. optional raised feature", 1
        )[1].split("# 5. dish or bump", 1)[0]
        self.assertIn("JoinFeatureOperation", raised_block)
        self.assertNotIn("combineFeatures", raised_block)

    def test_print_profiles_use_fine_nozzle_matte_pla_and_regular_supports(self):
        machine = self.profile_script_values["MACHINE_NAME"]
        process = self.profile_script_values["PROCESS_NAME"]
        filament = self.profile_script_values["FILAMENT_NAME"]
        settings = self.profile_script_values["EXPECTED_SETTINGS"]
        self.assertIn("0.2 nozzle", machine)
        self.assertIn("0.2 nozzle", process)
        self.assertIn("PLA Matte", filament)
        self.assertEqual(settings["enable_support"], "1")
        self.assertEqual(settings["support_type"], "normal(auto)")
        self.assertEqual(settings["sparse_infill_density"], "100%")

    def test_catalog_permutations_are_named_and_inside_ranges(self):
        presets = assigned_literal(self.script_module, "CATALOG_PRESETS")
        self.assertEqual(len(presets), 12)
        self.assertEqual(len({slug for slug, _, _ in presets}), len(presets))
        ranges = {item["name"]: item for item in self.inputs}
        catalog_names = {
            "skirt_h", "taper_h", "cyl_dia", "cyl_h", "dish_depth", "wall",
            "edge_size",
        }
        for slug, raised_top, parameters in presets:
            with self.subTest(preset=slug):
                self.assertIsInstance(raised_top, bool)
                self.assertEqual(set(parameters), catalog_names)
                for name, value in parameters.items():
                    contract_name = "chamfer_top" if name == "edge_size" else name
                    self.assertGreaterEqual(value, ranges[contract_name]["minimum"])
                    self.assertLessEqual(value, ranges[contract_name]["maximum"])


if __name__ == "__main__":
    unittest.main()
