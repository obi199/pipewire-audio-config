# PipeWire Audio Device Configuration GUI

A simple graphical tool to configure USB audio devices on PipeWire with support for multi-channel audio, custom buffer sizes, sample rates, and ACP mode toggling.

## Overview

Configure your audio devices without touching configuration files:
- **Channels**: 2, 4, 6, 8, 12, or 16 channels
- **Sample Rate**: 44.1kHz to 192kHz  
- **Buffer Size**: Professional audio sizes (32-4096 samples)
- **ACP Mode**: Toggle stereo-only vs multi-channel mode

Tested on: Ubuntu, Debian, Fedora, Arch, MX Linux

## Quick Start

### Prerequisites
- PipeWire running (not PulseAudio)
- Python 3.6+
- PyQt5

### Install Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pyqt5
```

**Fedora:**
```bash
sudo dnf install python3 python3-qt5
```

**Arch:**
```bash
sudo pacman -S python python-pyqt5
```

### Run

```bash
./run-pipewire-config.sh
```

Or directly:
```bash
python3 pipewire-device-config.py
```

## Usage

1. **Select Device** - Choose an audio device from the dropdown
2. **View Settings** - Current configuration displayed automatically
3. **Configure**:
   - Select number of channels
   - Choose sample rate
   - Pick buffer size
   - Toggle ACP mode
4. **Save Profile** - Creates WirePlumber configuration
5. **Restart PipeWire** - Changes take effect

```bash
systemctl --user restart wireplumber
```

## Features

### Device Detection
Automatically finds all ALSA audio devices on your system

### Multi-Channel Support
- Stereo (2ch) for basic audio
- Surround (4-8ch) for gaming/movies
- Multi-channel (12-16ch) for professional audio and ADAT interfaces

### Buffer Size Control
Standard audio buffer sizes (32-4096 samples) with real-time latency calculation:
- 32 samples @ 48kHz = 0.67ms (extreme low-latency)
- 256 samples @ 48kHz = 5.33ms (balanced - default)
- 1024 samples @ 48kHz = 21.33ms (maximum stability)

See `BUFFER_SIZE_REFERENCE.md` for complete table.

### ACP Mode Toggle
- **Disabled**: Full device capabilities, multi-channel access
- **Enabled**: Stereo-only mode for compatibility

### Persistent Configuration
Saves settings to WirePlumber config files automatically:
```
~/.config/wireplumber/wireplumber.conf.d/50-device-*.conf
```

## Example: RME Babyface Pro Setup

For 12-channel ADAT operation:

1. Select "Babyface Pro" device
2. Set Channels: **12**
3. Set Sample Rate: **48000 Hz**
4. Set Buffer Size: **256 samples**
5. Set ACP Mode: **Disabled (Full Channels)**
6. Click "Save as Profile"
7. Restart: `systemctl --user restart wireplumber`

## Supported Devices

Works with any USB audio device that supports multi-channel operation:
- RME Babyface Pro / UFX series
- Focusrite Scarlett series
- MOTU Audio interfaces
- PreSonus Studio series
- Generic USB audio interfaces
- Built-in sound cards

## Troubleshooting

### "PipeWire not installed"
```bash
sudo apt install pipewire pipewire-pulse
systemctl --user start pipewire
```

### "No audio devices found"
Check if PipeWire is running:
```bash
systemctl --user status pipewire
pw-dump | head -20
```

### "PyQt5 not found"
```bash
# Ubuntu/Debian
sudo apt install python3-pyqt5

# Fedora
sudo dnf install python3-qt5

# Arch
sudo pacman -S python-pyqt5
```

### Changes not applying
After saving a profile:
1. Restart WirePlumber: `systemctl --user restart wireplumber`
2. Reconnect your audio device (unplug/replug or restart)
3. Check config was created: `ls ~/.config/wireplumber/wireplumber.conf.d/`

### Only stereo showing
- Make sure "ACP Mode" is set to "Disabled (Full Channels)"
- Not all devices support multi-channel in Class Compliant mode
- Check device documentation for supported channel counts

## Project Structure

```
pipewire-audio-config/
├── pipewire-device-config.py      # Main GUI application
├── run-pipewire-config.sh         # Launcher script
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── PIPEWIRE_CONFIG_README.md      # Detailed documentation
└── BUFFER_SIZE_REFERENCE.md       # Buffer size reference table
```

## Development

### Requirements
```bash
pip3 install -r requirements.txt
```

### Run in development
```bash
python3 pipewire-device-config.py
```

### Code Structure
- **DeviceDetector**: Background thread for device detection via `pw-dump`
- **PipeWireConfigGUI**: Main Qt5 window with controls
- Configuration saved to `~/.config/wireplumber/wireplumber.conf.d/`

## Tips & Tricks

### Lowest Latency Recording
- Buffer: 64-128 samples
- Rate: 48kHz or 96kHz
- Channels: Match your device
- ACP: Disabled

### Stable Playback
- Buffer: 512-1024 samples
- Rate: 48kHz
- Channels: 2 (stereo)
- ACP: Can be either

### Professional Studio
- Buffer: 128 samples
- Rate: 96kHz
- Channels: 12+ (for multi-track)
- ACP: Disabled

## License

MIT License - See LICENSE file for details

## Contributing

Issues and pull requests welcome!

## Resources

- [PipeWire Documentation](https://docs.pipewire.org/)
- [WirePlumber Configuration](https://github.com/PipeWire/wireplumber)
- [ALSA Documentation](https://www.alsa-project.org/)

## Changelog

### v1.0.0 (2026-11-09)
- Initial release
- Device detection and configuration
- Multi-channel support (2-16 channels)
- Buffer size control (32-4096 samples)
- ACP mode toggle
- WirePlumber profile saving
