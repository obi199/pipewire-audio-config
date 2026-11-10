"""Unit tests for headless CLI execution and flag handling."""

import io
import json
import unittest
from unittest.mock import patch, MagicMock
from pipewire_config.cli import run_cli, create_parser

MOCK_DEVICES = [
    {
        "id": 42,
        "name": "alsa_output.usb-RME_Babyface_Pro_12345-00.pro-output-0",
        "description": "RME Babyface Pro",
        "media_class": "Audio/Sink",
        "channels": 12,
        "rate": 48000,
        "alsa_path": "hw:2,0",
        "alsa_card": 2,
        "use_acp": False,
        "latency_ns": 5333333
    }
]


class TestCLI(unittest.TestCase):

    def test_parser_arguments(self):
        parser = create_parser()
        args = parser.parse_args(["--device", "Babyface", "--buffer", "128", "--rate", "96000", "--dry-run"])
        self.assertEqual(args.device, "Babyface")
        self.assertEqual(args.buffer, 128)
        self.assertEqual(args.rate, 96000)
        self.assertTrue(args.dry_run)

    @patch('pipewire_config.cli.detect_devices')
    def test_cli_list_json(self, mock_detect):
        mock_detect.return_value = MOCK_DEVICES
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            exit_code = run_cli(["--list", "--json"])
            self.assertEqual(exit_code, 0)
            data = json.loads(mock_stdout.getvalue())
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['description'], "RME Babyface Pro")

    @patch('pipewire_config.cli.detect_devices')
    def test_cli_dry_run_json(self, mock_detect):
        mock_detect.return_value = MOCK_DEVICES
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            exit_code = run_cli(["--device", "Babyface", "--buffer", "128", "--dry-run", "--json"])
            self.assertEqual(exit_code, 0)
            data = json.loads(mock_stdout.getvalue())
            self.assertEqual(data['buffer_size'], 128)
            self.assertEqual(data['channels'], 12)
            self.assertIn("monitor.alsa.rules", data['config_content'])

    @patch('pipewire_config.cli.detect_devices')
    def test_cli_nonexistent_device(self, mock_detect):
        mock_detect.return_value = MOCK_DEVICES
        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            exit_code = run_cli(["--device", "NonExistentSoundCard", "--buffer", "128"])
            self.assertEqual(exit_code, 1)
            self.assertIn("No device matching", mock_stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
