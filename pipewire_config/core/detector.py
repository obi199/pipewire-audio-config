"""PipeWire and ALSA audio device detection."""

import json
import subprocess
from typing import List, Dict, Any


def parse_pw_dump(pw_dump_output: str) -> List[Dict[str, Any]]:
    """Parse pw-dump JSON output and extract ALSA audio nodes."""
    devices = []
    try:
        data = json.loads(pw_dump_output)

        default_rate = 48000
        for obj in data:
            if obj.get('type') == 'PipeWire:Interface:Core':
                props = obj.get('info', {}).get('props', {})
                core_rate = props.get('default.clock.rate')
                if core_rate:
                    try:
                        default_rate = int(core_rate)
                    except (ValueError, TypeError):
                        default_rate = 48000

        for obj in data:
            if obj.get('type') == 'PipeWire:Interface:Node' and obj.get('version') == 3:
                props = obj.get('info', {}).get('props', {})

                # Only include ALSA audio devices
                if 'alsa' not in props.get('node.name', ''):
                    continue

                media_class = props.get('media.class', '')
                if media_class not in ['Audio/Sink', 'Audio/Source']:
                    continue

                device_rate = props.get('audio.rate', 0)
                if device_rate == 0:
                    device_rate = default_rate

                device = {
                    'id': obj.get('id'),
                    'name': props.get('node.name', 'Unknown'),
                    'description': props.get('node.description', 'Unknown'),
                    'media_class': media_class,
                    'channels': props.get('audio.channels', 0),
                    'rate': device_rate,
                    'alsa_path': props.get('api.alsa.path', ''),
                    'alsa_card': props.get('alsa.card', props.get('api.alsa.card', props.get('api.alsa.pcm.card'))),
                    'alsa_card_name': props.get('alsa.card_name', props.get('api.alsa.card.name', '')),
                    'use_acp': props.get('api.alsa.use-acp', False),
                    'position': props.get('audio.position', []),
                    'latency_ns': props.get('latency.internal.ns', 0),
                }
                devices.append(device)
    except json.JSONDecodeError:
        pass

    return devices


def detect_devices(timeout: int = 5) -> List[Dict[str, Any]]:
    """Execute pw-dump and return list of detected ALSA audio devices."""
    result = subprocess.run(
        ['pw-dump'],
        capture_output=True,
        text=True,
        timeout=timeout
    )
    if result.returncode != 0:
        raise RuntimeError(f"pw-dump failed with exit code {result.returncode}: {result.stderr}")
    return parse_pw_dump(result.stdout)
