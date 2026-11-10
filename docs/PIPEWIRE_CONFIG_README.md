# PipeWire Audio Device Configuration GUI

A modular graphical tool and command-line utility to configure audio devices in PipeWire: buffer sizes, sample rates, latency, ACP mode, and ALSA hardware input/output mixers.

## Features

- **Device Detection**: Automatically discovers all ALSA audio devices via PipeWire `pw-dump`
- **Channel Locking**: Locks to the device's physical hardware channel limit (read-only)
- **Sample Rate**: Clock frequencies from 44.1 kHz to 192 kHz
- **Buffer Size Control**: Standard sizes (32, 64, 128, 256, 512, 1024, 2048, 4096 samples) with real-time calculated latency
- **ACP Mode Toggle**: Enable/disable stereo-only mode vs full multi-channel access
- **Input & Output Hardware Mixers**: Real-time ALSA faders with independent Mute ("M") and Solo ("S") routing
- **Headless CLI**: Query and configure audio interfaces from terminal and automation scripts
- **Single-Instance IPC**: Enforces single-window execution via local socket IPC
- **Save & Apply**: Create persistent WirePlumber `.conf` files and apply changes immediately

## Installation

### 1. Install Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pyqt5
```

**Fedora:**
```bash
sudo dnf install python3 python3-qt5
```

**Arch Linux:**
```bash
sudo pacman -S python python-pyqt5
```

**MX Linux:**
```bash
sudo apt update
sudo apt install python3 python3-pyqt5
```

### 2. Launch Options

#### Desktop GUI
```bash
# Option 1: Using launcher script
./run-pipewire-config.sh

# Option 2: Direct module execution
python3 -m pipewire_config

# Option 3: Backward-compatible wrapper
python3 pipewire-device-config.py
```

#### Headless CLI
```bash
# List devices
python3 -m pipewire_config.cli --list

# Apply buffer size and restart WirePlumber
python3 -m pipewire_config.cli --device "Babyface" --buffer 128 --apply
```

#### Optional Package Installation
```bash
pip install -e .
pipewire-config       # Launches GUI
pipewire-config-cli   # Launches CLI
```

## How It Works

### Main Window

1. **Select Device** - Choose an audio device from the dropdown
2. **View Information** - Current settings displayed automatically
3. **Configure Settings**:
   - Channels: Number of audio channels (2-16)
   - Sample Rate: Recording/playback quality
   - Latency: Buffer size (lower = more responsive, higher = more stable)
   - ACP Mode: Disabled = full channels, Enabled = stereo only

### Buttons

- **Apply Configuration** - Shows what changes would be applied (preview only)
- **Save as Profile** - Creates a permanent WirePlumber configuration file
- **Reset to Default** - Reset device to factory defaults
- **Refresh** - Scan for new devices

## Understanding the Settings

### ACP Mode
- **Disabled (Recommended for multi-channel)**: Uses full device capabilities
- **Enabled**: Limits device to stereo (2 channels) for compatibility

### Channels
- **2**: Stereo (mono left + mono right)
- **4**: Quad surround
- **6**: 5.1 surround (stereo + center + LFE + rear)
- **8**: 7.1 surround or stereo + ADAT
- **12**: Full 7.1 + ADAT (ideal for RME Babyface Pro)
- **16**: Extended surround + ADAT

### Sample Rate
- **44100 Hz**: CD quality
- **48000 Hz**: Professional/USB standard
- **88200, 96000**: High quality
- **176400, 192000**: Highest quality (requires USB 2.0 or better)

### Buffer Size (Samples)
Standard audio buffer sizes used in professional audio:
- **32 samples**: Extremely low latency (~0.66ms @ 48kHz), but CPU intensive
- **64 samples**: Very low latency (~1.33ms @ 48kHz), for demanding applications
- **128 samples**: Low latency (~2.67ms @ 48kHz)
- **256 samples**: Balanced, recommended default (~5.33ms @ 48kHz)
- **512 samples**: Standard, stable (~10.66ms @ 48kHz)
- **1024 samples**: High stability (~21.33ms @ 48kHz)
- **2048+ samples**: Highest stability, higher latency

**For your Babyface Pro:**
- Low-latency monitoring: 32-64 samples
- Balanced recording: 128-256 samples
- Stable playback: 256-512 samples
- Maximum stability: 1024+ samples

Actual latency in ms = (Buffer Size) / (Sample Rate) × 1000
Example: 256 samples @ 48kHz = 256/48000 × 1000 = 5.33ms

## Applying Changes

After clicking "Save as Profile":

1. Configuration is saved to: `~/.config/wireplumber/wireplumber.conf.d/`
2. Restart WirePlumber:
   ```bash
   systemctl --user restart wireplumber
   ```
3. Reconnect your device (or restart it)
4. Changes take effect!

## Troubleshooting

### "PipeWire not installed"
Install PipeWire:
```bash
sudo apt install pipewire pipewire-pulse
```

### "No audio devices found"
Check if PipeWire is running:
```bash
systemctl --user status pipewire
```

Start it if needed:
```bash
systemctl --user start pipewire
```

### Changes not taking effect
Make sure to restart WirePlumber:
```bash
systemctl --user restart wireplumber
```

Then reconnect your audio device (unplug/replug USB, or restart).

### Device shows wrong channel count
The device may not support that many channels. Check what's available:
```bash
pw-dump | grep audio.channels | grep -i <device-name>
```

## Creating a Desktop Shortcut (Optional)

Create `~/.local/share/applications/pipewire-config.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=PipeWire Device Config
Comment=Configure audio device channels, sample rate, latency
Exec=sh -c 'cd ~ && python3 pipewire-device-config.py'
Icon=audio-card
Categories=Audio;Utility;
Terminal=false
```

Then search for "PipeWire Device Config" in your application menu.

## For Other Devices

This tool works with any USB audio device on PipeWire, not just RME Babyface Pro:
- Focusrite Scarlett
- MOTU Audio interfaces
- PreSonus interfaces
- Generic USB audio devices
- Built-in sound cards

## License

MIT - Free to use and modify

## Tips & Tricks

### For Lowest Latency Recording
- Set channels to match your device (usually 12 for Babyface Pro)
- Set sample rate to 48000 Hz
- Set buffer size to 64 or 128 samples (~1.3-2.7ms)
- Disable ACP mode

### For Stable Playback
- Set buffer size to 256-512 samples (~5-10ms)
- Disable ACP mode for full channels
- Use 48000 Hz or 96000 Hz
- Consider 1024 samples if experiencing dropouts

### Professional Recording Setup (Babyface Pro)
- Channels: 12
- Sample Rate: 96000 Hz
- Buffer Size: 128 samples (~1.33ms)
- ACP Mode: Disabled

### For Multiple Apps at Once (Advantage over ALSA)
With this config, multiple applications can use different channels simultaneously - a major advantage over ALSA mode.

## Questions?

For PipeWire docs: https://docs.pipewire.org/
