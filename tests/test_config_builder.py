"""Unit tests for WirePlumber configuration builder."""

import unittest
import tempfile
from pathlib import Path
from pipewire_config.core.config_builder import (
    generate_wireplumber_config,
    nearest_buffer_size,
    calculate_latency_ms,
    calculate_latency_ns,
    write_wireplumber_config,
)


class TestConfigBuilder(unittest.TestCase):

    def test_nearest_buffer_size(self):
        self.assertEqual(nearest_buffer_size(0), 256)
        self.assertEqual(nearest_buffer_size(30), 32)
        self.assertEqual(nearest_buffer_size(50), 64)
        self.assertEqual(nearest_buffer_size(240), 256)
        self.assertEqual(nearest_buffer_size(4000), 4096)

    def test_calculate_latency(self):
        self.assertEqual(calculate_latency_ms(256, 48000), (256 / 48000) * 1000.0)
        self.assertEqual(calculate_latency_ms(256, 0), 0.0)
        self.assertEqual(calculate_latency_ns(256, 48000), int((256 / 48000) * 1e9))
        self.assertEqual(calculate_latency_ns(256, 0), 0)

    def test_generate_wireplumber_config(self):
        config = generate_wireplumber_config(
            device_name="alsa_card.usb-RME_Babyface_Pro_12345-00",
            channels=12,
            rate=48000,
            latency_ns=5333333,
            use_acp=False,
            channel_names=["Main-L", "Main-R", "ADAT-1", "ADAT-2", "ADAT-3", "ADAT-4", "ADAT-5", "ADAT-6", "ADAT-7", "ADAT-8", "S/PDIF-L", "S/PDIF-R"],
            description="RME Babyface Pro",
            master_volume=90,
            master_muted=False
        )

        self.assertIn("monitor.alsa.rules", config)
        self.assertIn('node.name = "~alsa_.*usb-RME_Babyface_Pro_12345-00.*"', config)
        self.assertIn("audio.channels = 12", config)
        self.assertIn('audio.position = ["Main-L", "Main-R"', config)
        self.assertIn("audio.rate = 48000", config)
        self.assertIn("latency.internal.ns = 5333333", config)
        self.assertIn("api.alsa.use-acp = false", config)
        self.assertIn("# Master Volume: 90%", config)

    def test_write_wireplumber_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            conf_path = write_wireplumber_config("test_usb_device", "# Test Config", config_dir=tmp_path)
            self.assertTrue(conf_path.exists())
            self.assertEqual(conf_path.read_text(encoding='utf-8'), "# Test Config")
            self.assertEqual(conf_path.name, "50-device-test_usb_device.conf")


if __name__ == '__main__':
    unittest.main()
