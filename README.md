# PipeWire Audio Device Configuration GUI

A simple graphical tool to configure USB audio devices on PipeWire with support for multi-channel audio, custom buffer sizes, sample rates, and ACP mode toggling.

## Overview

Configure your audio devices without touching configuration files:
- **Channels**: Automatically uses device's maximum channels (read-only)
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

### Basic Workflow

1. **Select Device** - Choose an audio device from the dropdown
2. **View Settings** - Current configuration displayed automatically (including channel count)
3. **Configure**:
    - **Channels**: Displays device's native channel count (read-only)
    - **Sample Rate**: 44.1kHz to 192kHz (dropdown)
    - **Buffer Size**: 32-4096 samples (dropdown)
    - **ACP Mode**: Toggle between full channels and stereo-only
4. **Master Volume**: Adjust overall device volume (0-100%) with real-time wpctl control
5. **Restart WirePlumber**: Click button to apply buffer/sample rate changes

### Device Information

The app displays detailed device info including:
- **Channel Mapping**: Custom names for known devices (Babyface Pro: Main-L/R, ADAT-1-8, S/PDIF-L/R)
- **Standard Layout**: Generic channel names (FL, FR, FC, etc.) for unknown devices
- **Sample Rate**: Current device sample rate
- **ACP Mode**: Whether device is in stereo-only or full-channel mode

## Features

### Device Detection
Automatically finds all ALSA audio devices via pw-dump with real-time updates

### Master Volume Control
- **Real-time volume adjustment**: 0-100% slider with instant feedback
- **Mute button**: Toggle 🔊/🔇 with visual red background when muted
- **wpctl integration**: Changes apply immediately without restart

### Sample Rate Control
- **Dynamic adjustment**: Change between 44.1kHz to 192kHz
- **Auto-config**: Saves to WirePlumber config automatically
- **Latency recalculation**: Updates buffer latency based on sample rate
- **Supported rates**: 44100, 48000, 88200, 96000, 176400, 192000 Hz

### Buffer Size Control
Standard audio buffer sizes (32-4096 samples) with real-time latency calculation:
- 32 samples @ 48kHz = 0.67ms (extreme low-latency)
- 256 samples @ 48kHz = 5.33ms (balanced - default)
- 1024 samples @ 48kHz = 21.33ms (maximum stability)

See `BUFFER_SIZE_REFERENCE.md` for complete table.

### Multi-Channel Support
- Stereo (2ch) for basic audio
- Surround (4-8ch) for gaming/movies
- Multi-channel (12-16ch) for professional audio and ADAT interfaces
- **Automatic channel detection**: Always uses device's maximum channels
- **Custom device names**: Displays meaningful channel names for known devices (e.g., Babyface Pro shows Main-L/R, ADAT-1-8, S/PDIF-L/R)

### ACP Mode Toggle
- **Disabled**: Full device capabilities, multi-channel access
- **Enabled**: Stereo-only mode for compatibility

### One-Click WirePlumber Restart
- **Restart Button**: Apply buffer size and sample rate changes with one click
- **Status Messages**: Confirmation when changes are saved
- **Error Handling**: Gracefully handles restart failures

### Persistent Configuration
Saves settings to WirePlumber config files automatically:
```
~/.config/wireplumber/wireplumber.conf.d/50-device-*.conf
```

Config includes:
- Sample rate (audio.rate)
- Buffer size (latency.internal.ns)
- Channel configuration
- ACP mode setting
- Volume settings (for reference)

## Example: RME Babyface Pro Setup

For 12-channel ADAT operation:

1. **Select Device**: "Babyface Pro (Class Compliant Mode)"
2. **Adjust Settings**:
    - Sample Rate: **48000 Hz**
    - Buffer Size: **256 samples** (5.33ms)
    - ACP Mode: **Disabled (Full Channels)**
3. **Set Volume**: Master Volume slider to desired level (or leave at 100%)
4. **Apply Changes**: Click **"Restart WirePlumber"** button
5. **Verify**: Device info shows "Channel Mapping: Main-L, Main-R, ADAT-1-8, S/PDIF-L/R"

Changes take effect after restart completes! 🎉

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
After changing buffer size or sample rate:
1. Click **"Restart WirePlumber"** button in the GUI
2. Or manually restart: `systemctl --user restart wireplumber`
3. Check config was created: `ls ~/.config/wireplumber/wireplumber.conf.d/`

### Volume changes not working
- Make sure wpctl is installed: `which wpctl`
- Check device ID: `wpctl status`
- Try restarting PipeWire: `systemctl --user restart wireplumber`

### Only stereo showing
- Make sure "ACP Mode" is set to "Disabled (Full Channels)"
- Not all devices support multi-channel in Class Compliant mode
- Check device documentation for supported channel counts
- The app uses your device's actual maximum channels - if it shows 2ch, the device is limited to stereo

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

### v1.2.0 (2026-11-09) - Current
- **Changed**: Channels now read-only (always uses device's maximum)
- **Improved**: Simplified UI by removing manual channel selection
- **Improved**: Prevents user confusion about channel configuration

### v1.1.0 (2026-11-09)
- **New**: Sample rate control GUI with auto-config saving
- **New**: Master volume slider with real-time wpctl integration
- **New**: Master mute button with visual feedback (🔊/🔇)
- **New**: One-click WirePlumber restart button
- **New**: Custom device channel name display (Babyface Pro support)
- **Fixed**: Per-channel volume controls removed (not supported by wpctl)
- **Improved**: Auto-save buffer size and sample rate to WirePlumber config
- **Improved**: Device information display with channel mapping

### v1.0.0 (2026-11-09) - Initial Release
- Device detection and configuration
- Multi-channel support (2-16 channels)
- Buffer size control (32-4096 samples)
- ACP mode toggle
- WirePlumber profile saving
