"""Unit tests for ALSA mixer and wpctl controller."""

import unittest
from unittest.mock import patch, MagicMock
from pipewire_config.core.alsa_mixer import (
    get_alsa_card_index,
    get_input_gain,
    apply_input_gain,
    get_wpctl_device_id,
    apply_volume,
    apply_mute,
    get_wpctl_volume_and_mute
)


class TestAlsaMixer(unittest.TestCase):

    def test_get_alsa_card_index(self):
        dev1 = {'alsa_card': 3, 'alsa_path': 'hw:1,0'}
        self.assertEqual(get_alsa_card_index(dev1), 3)

        dev2 = {'alsa_path': 'hw:2,0'}
        self.assertEqual(get_alsa_card_index(dev2), 2)

        dev3 = {'alsa_path': 'hw:0'}
        self.assertEqual(get_alsa_card_index(dev3), 0)

        dev4 = {'alsa_path': 'front:2'}
        self.assertEqual(get_alsa_card_index(dev4), 2)

        dev5 = {'alsa.card': 2}
        self.assertEqual(get_alsa_card_index(dev5), 2)

        self.assertEqual(get_alsa_card_index({}), 0)

    @patch('subprocess.run')
    def test_get_input_gain(self, mock_run):
        mock_output = """
Simple mixer control 'Line-ADAT3-AN1',0
  Capabilities: pvolume pvolume-joined
  Playback channels: Mono
  Limits: Playback 0 - 65536
  Mono: Playback 32768 [50%]
"""
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
        val = get_input_gain(2, "Line-ADAT3-AN1")
        self.assertEqual(val, 32768)

        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertIsNone(get_input_gain(2, "InvalidControl"))

    @patch('subprocess.run')
    def test_apply_input_gain(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(apply_input_gain(2, "Line-AS1-AN1", 32768))
        mock_run.assert_called_once_with(
            ['amixer', '-c', '2', 'sset', 'Line-AS1-AN1', '50%'],
            capture_output=True,
            text=True,
            timeout=2
        )

    @patch('subprocess.run')
    def test_get_wpctl_device_id_and_cache(self, mock_run):
        status_output = """
Audio
 ├─ Devices:
 │      40. Built-in Audio
 │      41. RME Babyface Pro
 │
 ├─ Sinks:
 │  *   42. alsa_output.pci-0000_00_1f.3.analog-stereo
 │      48. RME Babyface Pro Output
 │
 ├─ Sources:
 │  *   49. RME Babyface Pro Input
"""
        mock_run.return_value = MagicMock(returncode=0, stdout=status_output)

        cache = {}
        node_id = get_wpctl_device_id("alsa_output.usb-RME_Babyface_Pro.pro-output-0", cache)
        self.assertIn(node_id, ("41", "48"))
        self.assertIn("alsa_output.usb-RME_Babyface_Pro.pro-output-0", cache)

        mock_run.reset_mock()
        cached_id = get_wpctl_device_id("alsa_output.usb-RME_Babyface_Pro.pro-output-0", cache)
        self.assertEqual(cached_id, node_id)
        mock_run.assert_not_called()

        # Direct dictionary with ID
        self.assertEqual(get_wpctl_device_id({'id': 74, 'name': 'dev'}), '74')
        # Numeric ID
        self.assertEqual(get_wpctl_device_id(74), '74')
        self.assertEqual(get_wpctl_device_id('74'), '74')

    @patch('subprocess.run')
    def test_get_wpctl_volume_and_mute(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="Volume: 0.75 [MUTED]\n")
        vol, muted = get_wpctl_volume_and_mute("74")
        self.assertEqual(vol, 75)
        self.assertTrue(muted)

        mock_run.return_value = MagicMock(returncode=0, stdout="Volume: 1.00\n")
        vol, muted = get_wpctl_volume_and_mute("74")
        self.assertEqual(vol, 100)
        self.assertFalse(muted)

    @patch('subprocess.run')
    def test_apply_volume_and_mute(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(apply_volume("48", 85))
        mock_run.assert_called_with(
            ['wpctl', 'set-volume', '48', '85%'],
            capture_output=True,
            text=True,
            timeout=2
        )

        self.assertTrue(apply_mute("48", True))
        mock_run.assert_called_with(
            ['wpctl', 'set-mute', '48', '1'],
            capture_output=True,
            text=True,
            timeout=2
        )


if __name__ == '__main__':
    unittest.main()
