"""ALSA mixer and wpctl runtime controller."""

import os
import re
import subprocess
from typing import Dict, Optional, Any, List


def get_alsa_card_index(device: Dict[str, Any]) -> int:
    """Dynamically determine the ALSA card index for the given device."""
    if not device:
        return 0

    # 1. Direct property from PipeWire if available
    for prop in ['alsa_card', 'alsa.card', 'api.alsa.card', 'api.alsa.pcm.card']:
        card_prop = device.get(prop)
        if card_prop is not None:
            try:
                return int(card_prop)
            except (ValueError, TypeError):
                pass

    # 2. Extract card index from alsa_path (e.g., "front:2", "hw:1,0", "hw:1", "surround51:2")
    alsa_path = device.get('alsa_path') or device.get('api.alsa.path', '')
    if alsa_path:
        match = re.search(r'(?:hw|front|surround\d+|default|plughw|card)?:(\d+)', alsa_path)
        if not match:
            match = re.search(r'hw:(\d+)', alsa_path) or re.search(r'(\d+)', alsa_path)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                pass

    # 3. Fallback: match card name from `aplay -l`
    card_name = device.get('alsa_card_name') or device.get('description', '') or device.get('name', '')
    if card_name:
        try:
            env = dict(os.environ, LC_ALL='C')
            res = subprocess.run(['aplay', '-l'], capture_output=True, text=True, timeout=3, env=env)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if 'card ' in line:
                        m_num = re.search(r'card\s+(\d+):', line)
                        if m_num:
                            c_idx = int(m_num.group(1))
                            for term in [device.get('alsa_card_name', ''), device.get('description', ''), device.get('name', '')]:
                                if term and any(
                                    token.lower() in line.lower()
                                    for token in re.findall(r'[a-zA-Z0-9]+', term)
                                    if len(token) >= 4 and token.lower() not in {'alsa', 'output', 'input', 'node', 'card', 'device', 'sink', 'source', 'usb', 'analog', 'stereo'}
                                ):
                                    return c_idx
        except Exception:
            pass

    return 0


def get_input_gain(card: int, control_name: str) -> Optional[int]:
    """Get current ALSA mixer control gain level using amixer, normalized to 0..65536."""
    try:
        cmd = ['amixer', '-c', str(card), 'sget', control_name]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            min_lim, max_lim = 0, 65536
            raw_val = None
            pct_val = None
            for line in result.stdout.splitlines():
                m_lim = re.search(r'Limits:\s*(?:Playback\s+|Capture\s+)?(\d+)\s*-\s*(\d+)', line)
                if m_lim:
                    min_lim = int(m_lim.group(1))
                    max_lim = int(m_lim.group(2))
                    continue
                if 'Capabilities:' in line:
                    continue
                m_pct = re.search(r'\[(\d+)%\]', line)
                if m_pct:
                    pct_val = int(m_pct.group(1))
                m_val = re.search(r'(?:Playback|Mono|Front Left|Front Right|Capture)?:\s*(?:Playback\s+)?(\d+)', line)
                if m_val:
                    raw_val = int(m_val.group(1))

            if raw_val is not None:
                if max_lim > min_lim:
                    scaled = int(round((raw_val - min_lim) / (max_lim - min_lim) * 65536))
                    return min(65536, max(0, scaled))
                return min(65536, max(0, raw_val))
            if pct_val is not None:
                return int(round((pct_val / 100.0) * 65536))
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return None


def apply_input_gain(card: int, control_name: str, value: int) -> bool:
    """Set ALSA mixer control gain level using amixer."""
    try:
        pct = max(0, min(100, int(round((value / 65536.0) * 100))))
        cmd = ['amixer', '-c', str(card), 'sset', control_name, f"{pct}%"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


# Aliases for generic mixer gain handling (both inputs and outputs)
get_fader_gain = get_input_gain
apply_fader_gain = apply_input_gain


def apply_startup_control_map(card: int, controls: List[Dict[str, Any]]) -> int:
    """Apply profile-defined ALSA control defaults using first available fallback key."""
    applied = 0
    for spec in controls or []:
        if not isinstance(spec, dict):
            continue
        raw_value = spec.get('value', 65536)
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            continue
        value = min(65536, max(0, value))

        keys = spec.get('keys')
        if not isinstance(keys, list):
            keys = [spec.get('key')] if spec.get('key') else []

        for key in keys:
            if not isinstance(key, str) or not key.strip():
                continue
            # Probe for control existence first; this avoids needless amixer errors
            # when fallback keys are profile alternatives for kernel naming variants.
            if get_fader_gain(card, key) is None:
                continue
            if apply_fader_gain(card, key, value):
                applied += 1
            break
    return applied


def get_wpctl_device_id(device_identifier: Any, cache: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Find wpctl device ID for volume/mute controls with caching.
    
    Accepts:
    - a device dict (with 'id', 'name', 'description')
    - a numeric node ID (int or str of digits)
    - a device name or description string
    """
    if isinstance(device_identifier, dict):
        if device_identifier.get('id') is not None:
            node_id = str(device_identifier['id'])
            if cache is not None:
                if 'name' in device_identifier:
                    cache[device_identifier['name']] = node_id
                if 'description' in device_identifier:
                    cache[device_identifier['description']] = node_id
            return node_id
        device_name = device_identifier.get('name') or device_identifier.get('description', '')
        device_desc = device_identifier.get('description', '')
    elif isinstance(device_identifier, (int, float)):
        return str(int(device_identifier))
    elif isinstance(device_identifier, str):
        if device_identifier.isdigit():
            return device_identifier
        device_name = device_identifier
        device_desc = ""
    else:
        return None

    if cache is not None and device_name in cache:
        return cache[device_name]
    if cache is not None and device_desc and device_desc in cache:
        return cache[device_desc]

    try:
        result = subprocess.run(['wpctl', 'status'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return None

        def extract_tokens(text: str) -> set:
            words = re.findall(r'[a-zA-Z0-9]+', text.lower())
            return {w for w in words if len(w) >= 3 and w not in {'alsa', 'output', 'input', 'node', 'card', 'device', 'sink', 'source', 'usb', 'pci'}}

        search_tokens = extract_tokens(device_name) | extract_tokens(device_desc)

        clean_dev = re.sub(r'[^a-zA-Z0-9]', '', device_name).lower()
        core_dev = re.sub(r'^(alsa_output|alsa_input|alsa_card)\.', '', device_name)
        core_dev = re.sub(r'\.[^.]+$', '', core_dev)
        clean_core = re.sub(r'[^a-zA-Z0-9]', '', core_dev).lower()
        clean_core_no_usb = re.sub(r'^usb', '', clean_core)

        in_audio_section = False
        target_section = False

        best_match_id = None
        best_match_score = 0

        for line in result.stdout.splitlines():
            if 'Audio' in line:
                in_audio_section = True
                continue
            if in_audio_section and ('Video' in line or 'Settings' in line):
                break

            if in_audio_section and ('Sinks:' in line or 'Sources:' in line or 'Devices:' in line):
                target_section = True
                continue

            if in_audio_section and target_section and ('Filters:' in line or 'Streams:' in line):
                target_section = False
                continue

            if in_audio_section and target_section:
                match = re.search(r'(\d+)\.\s+(.*)', line)
                if match:
                    node_id = match.group(1)
                    node_desc = match.group(2).strip()
                    clean_desc = re.sub(r'[^a-zA-Z0-9]', '', node_desc).lower()

                    if (clean_core and (clean_core in clean_desc or clean_desc in clean_core)) or \
                       (clean_core_no_usb and (clean_core_no_usb in clean_desc or clean_desc in clean_core_no_usb)) or \
                       (clean_dev and (clean_dev in clean_desc or clean_desc in clean_dev)):
                        if cache is not None:
                            cache[device_name] = node_id
                        return node_id

                    line_tokens = extract_tokens(node_desc)
                    overlap = search_tokens & line_tokens
                    if len(overlap) > best_match_score:
                        best_match_score = len(overlap)
                        best_match_id = node_id

        if best_match_id and best_match_score > 0:
            if cache is not None:
                cache[device_name] = best_match_id
            return best_match_id
    except Exception:
        pass

    return None


def apply_volume(wpctl_id: str, volume_percent: int) -> bool:
    """Apply volume percentage using wpctl."""
    try:
        result = subprocess.run(
            ['wpctl', 'set-volume', str(wpctl_id), f"{volume_percent}%"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.returncode == 0
    except Exception:
        return False


def apply_mute(wpctl_id: str, muted: bool) -> bool:
    """Apply mute state using wpctl."""
    try:
        result = subprocess.run(
            ['wpctl', 'set-mute', str(wpctl_id), '1' if muted else '0'],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.returncode == 0
    except Exception:
        return False


def get_wpctl_volume_and_mute(wpctl_id: str) -> tuple[int, bool]:
    """Get current volume percentage and mute status from wpctl."""
    try:
        res = subprocess.run(['wpctl', 'get-volume', str(wpctl_id)], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            output = res.stdout.strip()
            muted = '[MUTED]' in output
            m = re.search(r'Volume:\s*([0-9.]+)', output)
            if m:
                vol_float = float(m.group(1))
                vol_pct = int(round(vol_float * 100))
                return min(100, max(0, vol_pct)), muted
    except Exception:
        pass
    return 100, False
