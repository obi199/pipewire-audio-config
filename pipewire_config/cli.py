"""Headless command-line interface for PipeWire audio configuration."""

import sys
import json
import argparse
from typing import List, Optional

from . import __version__
from .core.detector import detect_devices
from .core.config_builder import (
    generate_wireplumber_config,
    write_wireplumber_config,
    nearest_buffer_size,
    calculate_latency_ms,
    get_config_path,
    BUFFER_SIZES
)
from .core.service import restart_wireplumber
from .profiles.loader import get_profile_loader


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="pipewire-config-cli",
        description="Headless PipeWire & WirePlumber audio device configuration utility."
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-l", "--list", action="store_true", help="List all detected PipeWire ALSA audio devices")
    parser.add_argument("-d", "--device", type=str, help="Target device name or description pattern (substring match)")
    parser.add_argument("-b", "--buffer", type=int, choices=BUFFER_SIZES, help="Set audio buffer size in samples")
    parser.add_argument("-r", "--rate", type=int, choices=[44100, 48000, 88200, 96000, 176400, 192000], help="Set sample rate in Hz")
    parser.add_argument("--acp", choices=["enable", "disable"], help="Enable or disable ALSA ACP mode (stereo-only limit)")
    parser.add_argument("--save", action="store_true", help="Write configuration file without restarting WirePlumber")
    parser.add_argument("-a", "--apply", action="store_true", help="Write configuration file and restart WirePlumber")
    parser.add_argument("--restart", action="store_true", help="Restart WirePlumber service immediately")
    parser.add_argument("--dry-run", action="store_true", help="Preview generated WirePlumber configuration without writing")
    parser.add_argument("--json", action="store_true", help="Output information in JSON format")

    return parser


def find_device(devices: List[dict], pattern: str) -> Optional[dict]:
    """Find device by name or description pattern."""
    pattern_lower = pattern.lower()
    for dev in devices:
        if pattern_lower in dev.get('description', '').lower() or pattern_lower in dev.get('name', '').lower():
            return dev
    return None


def run_cli(args: Optional[List[str]] = None) -> int:
    """Execute command-line interface logic."""
    parser = create_parser()
    parsed = parser.parse_args(args)

    if parsed.restart:
        print("Restarting WirePlumber service...")
        success, message = restart_wireplumber(timeout=10, wait_delay=1.0)
        if success:
            print("✓ WirePlumber restarted successfully.")
            return 0
        else:
            print(f"✗ Error: {message}", file=sys.stderr)
            return 1

    try:
        devices = detect_devices(timeout=5)
    except Exception as e:
        print(f"✗ Failed to detect PipeWire devices: {str(e)}", file=sys.stderr)
        return 1

    if parsed.list or (not parsed.device and not parsed.dry_run and not parsed.save and not parsed.apply):
        if parsed.json:
            print(json.dumps(devices, indent=2))
        else:
            print(f"Detected {len(devices)} ALSA audio devices:\n")
            for idx, dev in enumerate(devices, 1):
                direction = "Output" if dev['media_class'] == 'Audio/Sink' else "Input"
                rate = dev.get('rate', 48000)
                lat_ns = dev.get('latency_ns', 0)
                buf = int(round((lat_ns / 1e9) * rate)) if rate > 0 else 256
                buf = nearest_buffer_size(buf)
                lat_ms = calculate_latency_ms(buf, rate)

                print(f"[{idx}] {dev['description']}")
                print(f"    Node Name:   {dev['name']}")
                print(f"    Type:        {direction}")
                print(f"    Channels:    {dev['channels']}")
                print(f"    Sample Rate: {rate} Hz")
                print(f"    Buffer Size: {buf} samples (~{lat_ms:.2f} ms)")
                print(f"    ALSA Path:   {dev.get('alsa_path') or 'N/A'}")
                print(f"    ACP Mode:    {'Enabled' if dev.get('use_acp') else 'Disabled'}")
                print()
        return 0

    if parsed.device:
        target_dev = find_device(devices, parsed.device)
        if not target_dev:
            print(f"✗ Error: No device matching '{parsed.device}' found.", file=sys.stderr)
            return 1

        loader = get_profile_loader()
        rate = parsed.rate or target_dev.get('rate', 48000) or 48000

        if parsed.buffer:
            buffer_size = parsed.buffer
        else:
            lat_ns = target_dev.get('latency_ns', 0)
            buf_samples = int(round((lat_ns / 1e9) * rate)) if rate > 0 else 256
            buffer_size = nearest_buffer_size(buf_samples)

        latency_ns = int((buffer_size / rate) * 1e9)

        if parsed.acp:
            use_acp = (parsed.acp == "enable")
        else:
            use_acp = bool(target_dev.get('use_acp', False))

        channels = target_dev.get('channels', 2)
        direction = 'outputs' if target_dev['media_class'] == 'Audio/Sink' else 'inputs'
        custom_names = loader.get_channel_names(target_dev['description'], direction)

        config_text = generate_wireplumber_config(
            device_name=target_dev['name'],
            channels=channels,
            rate=rate,
            latency_ns=latency_ns,
            use_acp=use_acp,
            channel_names=custom_names,
            description=target_dev['description']
        )

        if parsed.dry_run:
            if parsed.json:
                out = {
                    "device": target_dev['description'],
                    "node_name": target_dev['name'],
                    "channels": channels,
                    "rate": rate,
                    "buffer_size": buffer_size,
                    "latency_ms": calculate_latency_ms(buffer_size, rate),
                    "use_acp": use_acp,
                    "config_path": str(get_config_path(target_dev['name'])),
                    "config_content": config_text
                }
                print(json.dumps(out, indent=2))
            else:
                print(f"--- Configuration Preview for {target_dev['description']} ---")
                print(config_text)
            return 0

        if parsed.save or parsed.apply:
            try:
                conf_file = write_wireplumber_config(target_dev['name'], config_text)
                print(f"✓ Configuration written to: {conf_file}")
            except Exception as e:
                print(f"✗ Failed to write configuration: {str(e)}", file=sys.stderr)
                return 1

            if parsed.apply:
                print("Restarting WirePlumber...")
                success, msg = restart_wireplumber(timeout=10, wait_delay=1.0)
                if success:
                    print("✓ WirePlumber restarted successfully.")
                else:
                    print(f"✗ Warning: {msg}", file=sys.stderr)
                    return 1
            return 0

        # If device specified without action flags, print its status
        lat_ms = calculate_latency_ms(buffer_size, rate)
        print(f"Device:      {target_dev['description']}")
        print(f"Node Name:   {target_dev['name']}")
        print(f"Channels:    {channels}")
        print(f"Sample Rate: {rate} Hz")
        print(f"Buffer Size: {buffer_size} samples (~{lat_ms:.2f} ms)")
        print(f"ACP Mode:    {'Enabled' if use_acp else 'Disabled'}")
        print(f"Config File: {get_config_path(target_dev['name'])}")
        return 0

    return 0


def main():
    """CLI entry point."""
    sys.exit(run_cli())


if __name__ == '__main__':
    main()
