"""Unit tests for device profile loader and schema validation."""

import json
import unittest
import tempfile
from pathlib import Path
from pipewire_config.profiles.loader import ProfileLoader


class TestProfileLoader(unittest.TestCase):

    def test_builtin_profile_loading(self):
        loader = ProfileLoader()
        profiles = loader.get_all_profiles()
        self.assertIn("Babyface Pro", profiles)

        bf_profile = loader.get_profile_for_device("RME Babyface Pro Output")
        self.assertIsNotNone(bf_profile)
        self.assertEqual(bf_profile['name'], "RME Babyface Pro - Physical I/O")
        self.assertEqual(bf_profile['channels'], 12)
        self.assertTrue(bf_profile['has_input_mixer'])

        outputs = loader.get_channel_names("RME Babyface Pro", "outputs")
        self.assertIsNotNone(outputs)
        self.assertEqual(len(outputs), 12)
        self.assertEqual(outputs[0], "Main-L")
        self.assertEqual(outputs[-1], "S/PDIF-R")

        mixer_controls = loader.get_mixer_controls("RME Babyface Pro")
        self.assertIsNotNone(mixer_controls)
        self.assertIn("analog", mixer_controls)
        self.assertIn("spdif", mixer_controls)
        self.assertIn("adat", mixer_controls)

    def test_user_profile_override(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            user_dir = Path(tmpdir)
            custom_profile = {
                "name": "Custom Focusrite Interface",
                "match_description": "Scarlett 18i20",
                "channels": 18,
                "has_input_mixer": False,
                "layout": {
                    "outputs": [f"Out-{i}" for i in range(1, 19)],
                    "inputs": [f"In-{i}" for i in range(1, 19)]
                }
            }
            (user_dir / "scarlett.json").write_text(json.dumps(custom_profile), encoding='utf-8')

            loader = ProfileLoader(user_profiles_dir=user_dir)
            matched = loader.get_profile_for_device("Focusrite Scarlett 18i20 USB")
            self.assertIsNotNone(matched)
            self.assertEqual(matched['name'], "Custom Focusrite Interface")
            self.assertEqual(matched['channels'], 18)
            self.assertEqual(len(loader.get_channel_names("Focusrite Scarlett 18i20", "outputs")), 18)


if __name__ == '__main__':
    unittest.main()
