# Project Setup & Quick Reference

## Project Location
```
/home/pete/CLionProjects/pipewire-audio-config/
```

## Files Overview

| File | Purpose |
|------|---------|
| `pipewire-device-config.py` | Main GUI application (415 lines) |
| `run-pipewire-config.sh` | Launcher script with dependency checks |
| `QUICKSTART.sh` | Quick start guide script |
| `README.md` | Main documentation |
| `PIPEWIRE_CONFIG_README.md` | Detailed configuration guide |
| `BUFFER_SIZE_REFERENCE.md` | Buffer size reference table |
| `requirements.txt` | Python dependencies |
| `LICENSE` | MIT License |
| `.gitignore` | Git ignore rules |

## Quick Start

### 1. Install Dependencies
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pyqt5

# Fedora
sudo dnf install python3 python3-qt5

# Arch
sudo pacman -S python python-pyqt5
```

### 2. Run the Application
```bash
cd /home/pete/CLionProjects/pipewire-audio-config
./run-pipewire-config.sh
```

Or directly:
```bash
python3 /home/pete/CLionProjects/pipewire-audio-config/pipewire-device-config.py
```

### 3. Configure Your Device
1. Select device from dropdown
2. Set channels (2, 4, 6, 8, 12, or 16)
3. Choose sample rate
4. Select buffer size
5. Toggle ACP mode
6. Click "Save as Profile"

### 4. Apply Changes
```bash
systemctl --user restart wireplumber
```

## For RME Babyface Pro

Recommended settings for 12-channel operation:

| Setting | Value |
|---------|-------|
| Channels | 12 |
| Sample Rate | 48000 Hz (or 96000) |
| Buffer Size | 256 samples (5.33ms) |
| ACP Mode | Disabled |

Then save and restart WirePlumber.

## File Locations

### Configuration Files
After saving a profile, look here:
```
~/.config/wireplumber/wireplumber.conf.d/
```

### Application Location
```
/home/pete/CLionProjects/pipewire-audio-config/pipewire-device-config.py
```

## Git Repository

Local git repo initialized:
```bash
cd /home/pete/CLionProjects/pipewire-audio-config
git log --oneline
```

To push to GitHub:
```bash
git remote add origin https://github.com/USERNAME/pipewire-audio-config.git
git branch -M main
git push -u origin main
```

## Development

### Run tests/checks
```bash
# Check Python syntax
python3 -m py_compile pipewire-device-config.py

# Run the application
python3 pipewire-device-config.py
```

### Code Structure
- **DeviceDetector class**: Background thread for device detection
- **PipeWireConfigGUI class**: Main Qt5 application window
- **update_device_info()**: Displays current device settings
- **save_profile()**: Generates WirePlumber config files

## Troubleshooting

### Application won't start
1. Check PipeWire is running: `systemctl --user status pipewire`
2. Verify PyQt5: `python3 -c "import PyQt5"`
3. Check Python version: `python3 --version` (needs 3.6+)

### No devices shown
```bash
# Check devices manually
pw-dump | grep "media.class"

# Check PipeWire status
pw-cli list-objects Node
```

### Configuration not applied
1. Save profile in GUI
2. Restart WirePlumber: `systemctl --user restart wireplumber`
3. Reconnect device (unplug/replug)
4. Verify config: `ls ~/.config/wireplumber/wireplumber.conf.d/`

## Documentation

| Document | Content |
|----------|---------|
| README.md | Main overview and features |
| PIPEWIRE_CONFIG_README.md | Detailed usage guide |
| BUFFER_SIZE_REFERENCE.md | Buffer sizes and latency reference |
| SETUP.md | This file - setup instructions |

## Version

**v1.0.0** - Initial release
- Multi-channel audio support (2-16 channels)
- Standard buffer size control
- Cross-distro compatibility
- WirePlumber profile generation

## Support

- PipeWire Docs: https://docs.pipewire.org/
- WirePlumber: https://github.com/PipeWire/wireplumber
- ALSA: https://www.alsa-project.org/

---

Last updated: 2026-11-09
