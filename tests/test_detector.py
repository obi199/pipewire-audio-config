"""Unit tests for PipeWire device detection parsing."""

import json
import unittest
from pipewire_config.core.detector import parse_pw_dump

SAMPLE_PW_DUMP = json.dumps([
    {
        "id": 0,
        "type": "PipeWire:Interface:Core",
        "version": 3,
        "info": {
            "props": {
                "default.clock.rate": 48000
            }
        }
    },
    {
        "id": 42,
        "type": "PipeWire:Interface:Node",
        "version": 3,
        "info": {
            "props": {
                "node.name": "alsa_output.usb-RME_Babyface_Pro_12345-00.pro-output-0",
                "node.description": "RME Babyface Pro",
                "media.class": "Audio/Sink",
                "audio.channels": 12,
                "audio.rate": 48000,
                "api.alsa.path": "hw:2,0",
                "api.alsa.card": 2,
                "api.alsa.use-acp": False,
                "latency.internal.ns": 5333333
            }
        }
    },
    {
        "id": 43,
        "type": "PipeWire:Interface:Node",
        "version": 3,
        "info": {
            "props": {
                "node.name": "alsa_input.usb-RME_Babyface_Pro_12345-00.pro-input-0",
                "node.description": "RME Babyface Pro",
                "media.class": "Audio/Source",
                "audio.channels": 12,
                "audio.rate": 48000,
                "api.alsa.path": "hw:2,0",
                "api.alsa.card": 2,
                "api.alsa.use-acp": False,
                "latency.internal.ns": 5333333
            }
        }
    },
    {
        "id": 99,
        "type": "PipeWire:Interface:Node",
        "version": 3,
        "info": {
            "props": {
                "node.name": "v4l2_input.pci-0000_00_14.0-usb-0_4_1.0",
                "node.description": "Webcam Video",
                "media.class": "Video/Source"
            }
        }
    }
])


class TestDetector(unittest.TestCase):

    def test_parse_pw_dump(self):
        devices = parse_pw_dump(SAMPLE_PW_DUMP)
        self.assertEqual(len(devices), 2)

        sink = devices[0]
        self.assertEqual(sink['id'], 42)
        self.assertEqual(sink['name'], "alsa_output.usb-RME_Babyface_Pro_12345-00.pro-output-0")
        self.assertEqual(sink['description'], "RME Babyface Pro")
        self.assertEqual(sink['media_class'], "Audio/Sink")
        self.assertEqual(sink['channels'], 12)
        self.assertEqual(sink['rate'], 48000)
        self.assertEqual(sink['alsa_card'], 2)
        self.assertEqual(sink['alsa_path'], "hw:2,0")
        self.assertFalse(sink['use_acp'])

        source = devices[1]
        self.assertEqual(source['id'], 43)
        self.assertEqual(source['media_class'], "Audio/Source")


if __name__ == '__main__':
    unittest.main()
