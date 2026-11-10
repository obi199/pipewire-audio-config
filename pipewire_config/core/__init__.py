"""Core backend adapters and utilities for PipeWire and WirePlumber configuration."""

from .detector import detect_devices, parse_pw_dump
from .config_builder import (
    generate_wireplumber_config,
    nearest_buffer_size,
    calculate_latency_ms,
    calculate_latency_ns,
    get_config_path,
    write_wireplumber_config,
)
from .alsa_mixer import (
    get_alsa_card_index,
    get_input_gain,
    apply_input_gain,
    get_fader_gain,
    apply_fader_gain,
    get_wpctl_device_id,
    apply_volume,
    apply_mute,
    get_wpctl_volume_and_mute,
)
from .service import restart_wireplumber

__all__ = [
    "detect_devices",
    "parse_pw_dump",
    "generate_wireplumber_config",
    "nearest_buffer_size",
    "calculate_latency_ms",
    "calculate_latency_ns",
    "get_config_path",
    "write_wireplumber_config",
    "get_alsa_card_index",
    "get_input_gain",
    "apply_input_gain",
    "get_fader_gain",
    "apply_fader_gain",
    "get_wpctl_device_id",
    "apply_volume",
    "apply_mute",
    "get_wpctl_volume_and_mute",
    "restart_wireplumber",
]
