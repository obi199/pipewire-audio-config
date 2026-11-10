# PipeWire Audio Device Configuration GUI

A modular graphical utility and command-line tool to configure USB and pro-audio interfaces on PipeWire and WirePlumber with support for multi-channel audio, custom buffer sizes, sample rates, ACP mode toggling, and hardware-level ALSA input/output mixer consoles.

> **Hardware Note**: This application was programmed and tested specifically for the **RME Babyface Pro** (in Class Compliant mode, featuring dedicated hardware preamp and mixer controls). Other audio cards and USB interfaces also work seamlessly for buffer sizes, sample rates, ACP mode switching, and channel configuration, with optional custom JSON profile support.

## Overview

Configure your audio devices without manually editing configuration files:
- **Channels**: Automatically locks to the device's native hardware maximum (read-only)
- **Sample Rate**: Clock frequencies from 44.1 kHz to 192 kHz
- **Buffer Size**: Professional audio buffer sizes (32–4096 samples) with real-time calculated latency
- **ACP Mode**: Toggle between stereo-only compatibility and full multi-channel hardware access
- **Input & Output Hardware Mixers**: Real-time ALSA mixer consoles with faders, preamps, mute ("M"), and solo ("S") routing
- **Single-Instance Management**: Prevents duplicate instances and focuses the running window
- **Headless CLI**: Automate and script audio device settings in terminal environments

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

**Desktop GUI:**
```bash
# Via launcher script
./run-pipewire-config.sh

# Or as a Python module
python3 -m pipewire_config

# Or via wrapper script
python3 pipewire-device-config.py
```

**Headless CLI (for scripts & automation):**
```bash
# List devices
python3 -m pipewire_config.cli --list

# Inspect device latency
python3 -m pipewire_config.cli --device "Babyface"

# Set buffer size and restart WirePlumber
python3 -m pipewire_config.cli --device "Babyface" --buffer 128 --apply
```

**Optional System Install:**
```bash
pip install -e .

# Then launch directly anywhere:
pipewire-config       # GUI
pipewire-config-cli   # CLI
```

## Usage

### Basic Workflow

1. **Select Device** - Choose an audio interface from the dropdown
2. **View Device Configuration** - Active hardware ALSA path, sample rate, buffer size, and calculated latency (`ms`) update dynamically
3. **Configure Latency & Clocks**:
    - **Channels**: Displays device's native channel count (read-only)
    - **Sample Rate**: 44.1 kHz to 192 kHz (dropdown)
    - **Buffer Size**: 32–4096 samples (dropdown)
    - **ACP Mode**: Toggle between full channels and stereo-only
4. **Hardware Mixer Adjustments (Real-Time)**:
    - **Input Levels**: Adjust analog preamp gains (Mic 1/2, Inst 3/4), analog line inputs, S/PDIF, and ADAT optical inputs with independent Mute ("M") and Solo ("S") buttons
    - **Output Levels**: Adjust coupled stereo Main Out (AN1/2), Phones (PH3/4), S/PDIF, and ADAT outputs with independent Mute ("M") and Solo ("S") buttons
5. **Apply & Restart WirePlumber**: Click to generate configuration rules and restart WirePlumber to apply buffer size or sample clock changes

### Dynamic Hardware Mixer Consoles

When an interface with supported ALSA mixer controls is selected (such as the RME Babyface Pro), the unified single-window layout displays:
- **Input Levels Mixer**: Horizontal scrollable console controlling hardware analog preamps, analog line inputs, digital S/PDIF, and ADAT optical lines.
- **Output Levels Mixer**: Direct hardware output attenuation, including coupled stereo Main Out (AN1/2), stereo Phones, S/PDIF, and ADAT digital outputs.
- **Mute ("M") & Solo ("S") Routing**: Isolate individual channels or silence paths instantly without disturbing other fader levels.
- **Debounced ALSA Dispatch**: Fast slider movements are debounced into 40ms batches to eliminate CPU process spikes.

## Features

### Device Detection & Dynamic Card Resolution
Automatically detects all ALSA audio sinks and sources via `pw-dump` JSON parsing. Dynamically resolves target ALSA card indices from PipeWire node paths (`front:X`, `hw:X,Y`) to prevent targeting inactive MIDI interfaces.

### Hardware Input & Output Mixers
- **Real-Time Faders**: 0–100% gain sliders mapped to hardware mixer controls via `amixer`
- **Dynamic Limit Scaling**: Automatically scales custom ALSA control limits (e.g. 0–65 dB microphone preamps) to normalized slider percentages
- **Per-Channel Mute**: Toggle "M" with visual red highlighting; remembers original fader volume when unmuted
- **Per-Channel Solo**: Toggle "S" with visual amber highlighting to isolate channels and suppress background inputs
- **Coupled Stereo Main Out**: Main Analog Outputs (AN1/AN2) adjust in lockstep

### Real-Time Latency Calculation
- Dynamic latency calculation in milliseconds and sample count displayed directly beneath buffer size controls:
  - 32 samples @ 48kHz = 0.67ms (ultra low-latency)
  - 128 samples @ 48kHz = 2.67ms (recording standard)
  - 256 samples @ 48kHz = 5.33ms (balanced)
  - 1024 samples @ 48kHz = 21.33ms (maximum stability)

See [Buffer Size Reference](docs/BUFFER_SIZE_REFERENCE.md) for complete tables.

### Declarative Device Profiles
- Store device layouts, channel names, and mixer controls in declarative JSON profiles (`pipewire_config/profiles/`)
- User-extensible: drop custom profiles into `~/.config/pipewire-audio-config/profiles/` to support any audio interface without touching Python code
- Graceful fallback: unsupported interfaces receive standard spatial channel topologies and clean placeholder views

### Single-Instance IPC
- Uses local socket IPC (`QLocalServer` / `QLocalSocket`) to enforce a single running window
- Launching a second instance automatically raises and focuses the existing window

### Persistent Configuration
Saves settings to WirePlumber configuration rules:
```
~/.config/wireplumber/wireplumber.conf.d/50-device-*.conf
```

Configuration includes:
- Sample rate (`audio.rate`)
- Buffer size (`latency.internal.ns`)
- Channel configuration (`audio.channels`, `audio.position`)
- ACP mode setting (`api.alsa.use-acp`)

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

## Hardware Compatibility & Supported Devices

This utility was programmed and tested specifically for the **RME Babyface Pro** (in USB Class Compliant mode), featuring complete dedicated ALSA mixer controls, microphone preamp gain scaling, coupled stereo main output, and custom channel labels (AN1/2, PH3/4, S/PDIF, ADAT 1–8).

**Other audio interfaces and sound cards are also fully supported**:
- **Generic USB Interfaces & Sound Cards**: Any ALSA/PipeWire compatible device supports sample rate switching, buffer size / latency adjustments, ACP mode toggling, and standard multi-channel spatial layouts.
- **Custom Hardware Profiles**: New audio interfaces can have custom channel names and ALSA mixer faders defined simply by adding a JSON profile to `~/.config/pipewire-audio-config/profiles/` (or contributing to `pipewire_config/profiles/`).
- **Tested Device Families**:
  - **RME**: Babyface Pro / FS, Fireface / UFX series (Class Compliant mode)
  - **Focusrite**: Scarlett series (2i2, 4i4, 18i8, 18i20)
  - **MOTU**: UltraLite, M2/M4/M6, 8pre series
  - **PreSonus**: Studio / AudioBox series
  - **Behringer**: U-Phoria UMC series (UMC204HD, UMC404HD, UMC1820)
  - **Standard Built-in Sound Cards**: Realtek / Intel HDA stereo and surround outputs

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
├── pipewire_config/               # Core Python package
│   ├── __init__.py
│   ├── __main__.py               # python3 -m pipewire_config entry point
│   ├── cli.py                    # Headless CLI entry point
│   ├── core/                     # Pure Python system adapters
│   │   ├── detector.py           # pw-dump parsing & device discovery
│   │   ├── config_builder.py     # WirePlumber .conf SPA-JSON generator
│   │   ├── alsa_mixer.py         # Dynamic ALSA card resolution & amixer/wpctl
│   │   └── service.py            # WirePlumber systemd lifecycle manager
│   ├── profiles/                 # Declarative hardware profiles
│   │   ├── loader.py             # Profile discovery & schema validation
│   │   └── babyface_pro.json     # RME Babyface Pro declarative profile
│   └── ui/                       # PyQt5 Presentation Layer
│       ├── main_window.py        # Top-level window coordinator
│       └── widgets/
│           ├── config_panel.py   # Latency, sample rate, buffer size, ACP
│           ├── volume_panel.py   # Master volume & mute controls
│           └── fader_strip.py    # Scrollable input mixer with mute/solo
├── tests/                         # Automated test suite
│   ├── test_config_builder.py
│   ├── test_detector.py
│   ├── test_alsa_mixer.py
│   ├── test_loader.py
│   ├── test_cli.py
│   └── test_ui.py
├── pyproject.toml                 # Standard packaging metadata & entry points
├── pipewire-device-config.py      # Backward-compatible wrapper script
├── babyface_channels.py           # Legacy channel mappings (deprecated)
├── run-pipewire-config.sh         # Shell launcher script
├── setup.sh                       # Setup and installation script
├── QUICKSTART.sh                  # Quick start guide
├── requirements.txt               # Python dependencies
├── README.md                      # Overview and quick start guide
└── docs/                          # Detailed documentation
    ├── SETUP.md                   # Installation & setup guide
    ├── BUFFER_SIZE_REFERENCE.md   # Buffer size and latency table
    ├── BUFFER_SIZE_CHANGES.md     # How buffer size changes work
    ├── CHANNEL_LAYOUT.md          # Multi-channel layout documentation
    ├── BABYFACE_PRO_CHANNELS.md   # RME Babyface Pro specific guide
    ├── DEVICE_DETECTION.md        # Device detection mechanism
    ├── ACP_MODE_EXPLAINED.md      # ACP mode explanation
    ├── PIPEWIRE_CONFIG_README.md  # Detailed WirePlumber config guide
    └── PROJECT_STATUS.md          # Project roadmap & status
```

## Documentation

Detailed documentation is available in the [`docs/`](docs/) directory:

- [Setup & Installation Guide](docs/SETUP.md) - Detailed prerequisites, automated and manual installation instructions.
- [Buffer Size & Latency Reference](docs/BUFFER_SIZE_REFERENCE.md) - Complete latency tables across all sample rates (44.1kHz–192kHz).
- [Buffer Size Changes Explained](docs/BUFFER_SIZE_CHANGES.md) - Technical explanation of how PipeWire and WirePlumber apply buffer sizes.
- [Multi-Channel Layout Guide](docs/CHANNEL_LAYOUT.md) - Channel positioning, pro audio mappings, and surround topologies.
- [RME Babyface Pro Guide](docs/BABYFACE_PRO_CHANNELS.md) - Hardware channels, ADAT/SPDIF mappings, and ALSA mixer routing.
- [Device Detection](docs/DEVICE_DETECTION.md) - Deep dive into `pw-dump` JSON parsing and ALSA node enumeration.
- [ACP Mode Explained](docs/ACP_MODE_EXPLAINED.md) - Audio Codec Protocol vs pro-audio multi-channel operation.
- [WirePlumber Config Guide](docs/PIPEWIRE_CONFIG_README.md) - WirePlumber `.conf` SPA-JSON structure and syntax rules.
- [Project Status & Roadmap](docs/PROJECT_STATUS.md) - Feature checklist, architecture notes, and version roadmap.

## Development & Testing

### Running Tests
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

### Launching GUI in Development
```bash
python3 -m pipewire_config
```

### Launching CLI in Development
```bash
python3 -m pipewire_config.cli --help
```

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

### v1.3.0 (2026-11-10) - Current
- **New**: Modular Python package architecture (`pipewire_config`) with pure Python core backend services decoupled from GUI.
- **New**: Headless command-line interface (`pipewire_config.cli`) with `--list`, `--device`, `--buffer`, `--rate`, `--acp`, `--dry-run`, and `--json` support.
- **New**: Declarative JSON device profile schema (`pipewire_config/profiles/`) with user override support in `~/.config/pipewire-audio-config/profiles/`.
- **New**: Hardware Input Mixer console with 28 channels for Babyface Pro (Mic 1 & 2 preamp gains, Mic 1 & 2 L/R, Inst 3 & 4 preamp gains, Inst 3 & 4 L/R, S/PDIF L/R, and ADAT 1–8).
- **New**: Hardware Output Mixer console with coupled stereo Main Out (AN1/2), Phones (PH3/4), S/PDIF (AS1/2), and ADAT Outs 1–6 (ADAT3–8).
- **New**: Independent Mute ("M") and Solo ("S") buttons across all input and output fader channels.
- **New**: Single-instance application management via local socket IPC (`QLocalServer` / `QLocalSocket`).
- **New**: Dynamic ALSA sound card index resolution with multi-format path matching (`front:X`, `hw:X,Y`) to prevent inactive MIDI card targeting.
- **New**: Real-time calculated latency display integrated directly into Device Configuration.
- **New**: Comprehensive automated unit test suite with 22 tests covering core services, profile loading, and UI widget behaviors.

### v1.2.0 (2026-11-09)
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
