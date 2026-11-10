"""Device profile loader and schema discovery."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class ProfileLoader:
    """Discovers, validates, and loads device configuration profiles."""

    def __init__(self, user_profiles_dir: Optional[Path] = None):
        self.builtin_dir = Path(__file__).parent
        if user_profiles_dir is None:
            self.user_dir = Path.home() / '.config' / 'pipewire-audio-config' / 'profiles'
        else:
            self.user_dir = user_profiles_dir

        self._profiles: Dict[str, Dict[str, Any]] = {}
        self.reload()

    def reload(self) -> None:
        """Scan and load all built-in and user-defined JSON profiles."""
        self._profiles.clear()

        # 1. Load built-in profiles
        if self.builtin_dir.is_dir():
            for json_file in sorted(self.builtin_dir.glob('*.json')):
                self._load_file(json_file)

        # 2. Load user override profiles (overrides or extends built-ins)
        if self.user_dir.is_dir():
            for json_file in sorted(self.user_dir.glob('*.json')):
                self._load_file(json_file)

    def _load_file(self, path: Path) -> None:
        """Safely parse and validate a profile JSON file."""
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                return

            match_desc = data.get('match_description')
            name = data.get('name')
            if match_desc and name:
                self._profiles[match_desc] = data
        except Exception:
            pass

    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Return all loaded profiles keyed by match description."""
        return self._profiles.copy()

    def get_profile_for_device(self, description: str) -> Optional[Dict[str, Any]]:
        """Find the matching profile for a given device description."""
        if not description:
            return None

        desc_lower = description.lower()
        for match_key, profile in self._profiles.items():
            if match_key.lower() in desc_lower:
                return profile
        return None

    def get_channel_names(self, description: str, direction: str = 'outputs') -> Optional[List[str]]:
        """Retrieve custom channel names for a device and stream direction."""
        profile = self.get_profile_for_device(description)
        if not profile:
            return None

        layout = profile.get('layout') or profile.get('channel_names')
        if isinstance(layout, dict):
            return layout.get(direction)
        return None

    def get_mixer_controls(self, description: str) -> Optional[Dict[str, Any]]:
        """Retrieve mixer controls schema if supported by the device."""
        profile = self.get_profile_for_device(description)
        if profile and profile.get('has_input_mixer'):
            return profile.get('mixer_controls')
        return None


_default_loader: Optional[ProfileLoader] = None


def get_profile_loader() -> ProfileLoader:
    """Get the shared ProfileLoader instance."""
    global _default_loader
    if _default_loader is None:
        _default_loader = ProfileLoader()
    return _default_loader
