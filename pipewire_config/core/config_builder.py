"""WirePlumber configuration builder and serialization."""

import json
import re
from pathlib import Path
from typing import List, Optional

BUFFER_SIZES = [32, 64, 128, 256, 512, 1024, 2048, 4096]


def nearest_buffer_size(samples: int) -> int:
    """Find the nearest standard power-of-2 buffer size."""
    if samples <= 0:
        return 256
    return min(BUFFER_SIZES, key=lambda x: abs(x - samples))


def calculate_latency_ms(buffer_size: int, sample_rate: int) -> float:
    """Calculate latency in milliseconds given buffer size and sample rate."""
    if sample_rate <= 0:
        return 0.0
    return (buffer_size / sample_rate) * 1000.0


def calculate_latency_ns(buffer_size: int, sample_rate: int) -> int:
    """Calculate latency in nanoseconds given buffer size and sample rate."""
    if sample_rate <= 0:
        return 0
    return int((buffer_size / sample_rate) * 1e9)


def get_config_path(device_name: str, config_dir: Optional[Path] = None) -> Path:
    """Get the target configuration file path for a device."""
    if config_dir is None:
        config_dir = Path.home() / '.config' / 'wireplumber' / 'wireplumber.conf.d'
    
    clean_name = re.sub(r'^(alsa_output|alsa_input|alsa_card)\.', '', device_name)
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', clean_name)
    if not clean_name:
        clean_name = "audio-device"
    
    return config_dir / f"50-device-{clean_name}.conf"


def generate_wireplumber_config(
    device_name: str,
    channels: int,
    rate: int,
    latency_ns: int,
    use_acp: bool,
    channel_names: Optional[List[str]] = None,
    description: str = "",
    master_volume: int = 100,
    master_muted: bool = False
) -> str:
    """Produces canonical WirePlumber 50-device-<shortname>.conf string."""
    if 'usb' in device_name:
        parts = device_name.split('.')
        match_pattern = None
        for p in parts:
            if 'usb' in p:
                match_pattern = p
                break
        if not match_pattern:
            match_pattern = parts[-2] if len(parts) >= 2 else device_name
        device_pattern = f'~alsa_.*{match_pattern}.*'
    else:
        device_pattern = f'~alsa_.*{device_name}.*'

    position_map = {
        2: '[ "FL", "FR" ]',
        4: '[ "FL", "FR", "RL", "RR" ]',
        6: '[ "FL", "FR", "FC", "LFE", "RL", "RR" ]',
        8: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "SL", "SR" ]',
        12: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "FLC", "FRC", "RC", "SL", "SR", "TC" ]',
        16: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "FLC", "FRC", "RC", "SL", "SR", "TC", "TFL", "TFR", "TRL", "TRR" ]',
    }

    if channel_names and len(channel_names) == channels:
        position = json.dumps(channel_names)
    else:
        position = position_map.get(channels, '[ "FL", "FR" ]')

    buffer_samples = int(round((latency_ns / 1e9) * rate)) if rate > 0 else 256
    buffer_ms = (buffer_samples / rate * 1000) if rate > 0 else 0.0

    desc_line = f"# Device: {description}\n" if description else ""

    config = f"""# PipeWire Audio Device Configuration
{desc_line}# Auto-generated configuration
# Sample Rate: {rate} Hz
# Buffer Size: {buffer_samples} samples ({buffer_ms:.2f}ms @ {rate}Hz)
# Master Volume: {master_volume}%
# Master Mute: {"true" if master_muted else "false"}

monitor.alsa.rules = [
  {{
    matches = [
      {{
        node.name = "{device_pattern}"
      }}
    ]
    actions = {{
      update-props = {{
        api.alsa.use-acp = {str(use_acp).lower()}
        audio.channels = {channels}
        audio.position = {position}
        audio.rate = {rate}
        latency.internal.ns = {latency_ns}
        # Volume settings
        # Master volume: 0-100%
        # Master mute: true/false
      }}
    }}
  }}
]
"""
    return config


def write_wireplumber_config(device_name: str, content: str, config_dir: Optional[Path] = None) -> Path:
    """Write WirePlumber configuration file to disk atomically."""
    config_file = get_config_path(device_name, config_dir)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(content, encoding='utf-8')
    return config_file
