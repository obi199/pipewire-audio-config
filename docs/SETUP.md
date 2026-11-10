# Setup Guide - PipeWire Audio Config

Complete installation and setup instructions for all supported Linux distributions.

## Quick Start

```bash
# Navigate to project directory
cd ~/CLionProjects/pipewire-audio-config

# Run setup
./setup.sh

# Follow prompts - the script will:
# 1. Detect your Linux distribution
# 2. Check for required dependencies
# 3. Install missing packages (with your permission)
# 4. Configure permissions
# 5. Set up desktop menu entry
# 6. Run verification tests
```

## What Setup Does

### Phase 1: System Detection
- Reads `/etc/os-release` to identify your Linux distribution
- Detects OS name and version
- Exits with error if unable to detect system

### Phase 2: Package Manager Detection
Automatically detects and configures for:
- **apt** (Ubuntu, Debian, MX Linux)
- **dnf** (Fedora, RHEL, CentOS)
- **pacman** (Arch Linux)
- **pip3** (fallback for unknown systems)

### Phase 3: Dependency Checking
Verifies installation of:
- **Python 3.6+** - Core requirement
- **PyQt5** - GUI framework
- **PipeWire** - Audio server (optional but recommended)

### Phase 4: Installation
Installs any missing dependencies using your system's package manager

### Phase 5: File Verification
Ensures all required scripts are present:
- `pipewire-device-config.py` - Main GUI application
- `run-pipewire-config.sh` - Launcher script

### Phase 6: Permission Setup
Makes all scripts executable:
```bash
chmod +x pipewire-device-config.py
chmod +x run-pipewire-config.sh
chmod +x setup.sh
```

### Phase 7: Desktop Integration
Creates application menu entry at:
```
~/.local/share/applications/pipewire-audio-config.desktop
```

Updates desktop database so app appears in application menus

### Phase 8: Configuration Setup
Creates directory for WirePlumber configurations:
```
~/.config/wireplumber/wireplumber.conf.d/
```

### Phase 9: Verification Tests
Runs comprehensive verification:
- ✓ Python version
- ✓ PyQt5 installation
- ✓ PipeWire installation
- ✓ Main script exists
- ✓ Launcher script exists
- ✓ Desktop entry installed

---

## Installation by Distribution

### Ubuntu / Debian / MX Linux

```bash
./setup.sh
```

**Package Manager:** apt

**Packages Installed:**
- `python3` - Python interpreter
- `python3-pyqt5` - PyQt5 GUI framework
- `pipewire` - Audio server (optional)

**Sudo Access:** Required for `apt install`

### Fedora / RHEL / CentOS

```bash
./setup.sh
```

**Package Manager:** dnf

**Packages Installed:**
- `python3` - Python interpreter
- `python3-pyqt5` - PyQt5 GUI framework
- `pipewire` - Audio server (optional)

**Sudo Access:** Required for `dnf install`

### Arch Linux

```bash
./setup.sh
```

**Package Manager:** pacman

**Packages Installed:**
- `python` - Python interpreter
- `python-pyqt5` - PyQt5 GUI framework
- `pipewire` - Audio server (optional)

**Sudo Access:** Required for `pacman -S`

### Other Distributions

If your package manager isn't detected:

```bash
./setup.sh
```

**Fallback:** pip3

**Installation:**
- PyQt5 installed via `pip3 install --user PyQt5`
- You must install PipeWire manually using your package manager

---

## Usage After Installation

### Launch from Application Menu

1. Open your application menu/launcher
2. Search for "PipeWire Audio Config"
3. Click to launch

### Launch from Terminal

```bash
~/CLionProjects/pipewire-audio-config/run-pipewire-config.sh
```

### Run Setup Again

To update or re-run setup:

```bash
cd ~/CLionProjects/pipewire-audio-config
./setup.sh
```

---

## Uninstall

### Remove Application from Menu

```bash
./setup.sh --uninstall
```

This will:
- Remove desktop entry from application menu
- Update desktop database
- **Preserve** all configuration files

### Completely Remove

To remove all files:

```bash
rm -rf ~/CLionProjects/pipewire-audio-config
```

User configurations in `~/.config/wireplumber/wireplumber.conf.d/` are preserved.

---

## Troubleshooting

### "No supported package manager found"

Your distribution uses an unsupported package manager. Setup will fall back to pip3:
- PyQt5 will be installed via pip3
- You must install PipeWire manually

```bash
# Find your package manager
which apt dnf pacman zypper

# Or search for "pipewire" in your package manager GUI
```

### "Failed to install Python3"

Python3 may require manual installation:

```bash
# Ubuntu/Debian
sudo apt install python3 python3-dev

# Fedora
sudo dnf install python3 python3-devel

# Arch
sudo pacman -S python

# Then run setup again
./setup.sh
```

### "Failed to install PyQt5"

PyQt5 is essential. Try these options:

**Option 1: Via pip3**
```bash
pip3 install --user PyQt5
```

**Option 2: Manual package manager**
```bash
# Ubuntu/Debian
sudo apt install python3-pyqt5

# Fedora
sudo dnf install python3-pyqt5

# Arch
sudo pacman -S python-pyqt5
```

**Option 3: Run setup again**
```bash
./setup.sh
```

### "PipeWire not found"

PipeWire is required to use the application but optional during setup.

**If you have PipeWire:**
- It may not be in the PATH
- Ensure `pw-dump` is available: `which pw-dump`

**If you don't have PipeWire:**
- Install it from your package manager
- Or switch to PipeWire for audio (beyond this guide's scope)

```bash
# Ubuntu/Debian
sudo apt install pipewire

# Fedora
sudo dnf install pipewire

# Arch
sudo pacman -S pipewire
```

### "Desktop entry not created"

The desktop entry should be at:
```
~/.local/share/applications/pipewire-audio-config.desktop
```

Check if it exists:
```bash
ls -la ~/.local/share/applications/pipewire-audio-config.desktop
```

If missing, run setup again:
```bash
./setup.sh
```

### "GUI won't start"

Test GUI loading:

```bash
cd ~/CLionProjects/pipewire-audio-config
python3 -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"
```

If that fails, reinstall PyQt5:
```bash
./setup.sh
```

If it succeeds, try launching directly:
```bash
python3 pipewire-device-config.py
```

---

## Manual Installation

If you prefer to install manually:

### 1. Install Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pyqt5 pipewire
```

**Fedora:**
```bash
sudo dnf install python3 python3-pyqt5 pipewire
```

**Arch:**
```bash
sudo pacman -S python python-pyqt5 pipewire
```

### 2. Set Permissions

```bash
cd ~/CLionProjects/pipewire-audio-config
chmod +x pipewire-device-config.py
chmod +x run-pipewire-config.sh
chmod +x setup.sh
```

### 3. Create Desktop Entry

```bash
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/pipewire-audio-config.desktop << EOF
[Desktop Entry]
Type=Application
Name=PipeWire Audio Config
Comment=Configure audio device channels, sample rate, and buffer size
Exec=$HOME/CLionProjects/pipewire-audio-config/run-pipewire-config.sh
Icon=audio-card
Categories=Utility;AudioVideo;
Terminal=false
StartupNotify=true
EOF

# Update desktop database (if available)
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
```

### 4. Create Config Directory

```bash
mkdir -p ~/.config/wireplumber/wireplumber.conf.d/
```

### 5. Test Installation

```bash
# Test Python
python3 --version

# Test PyQt5
python3 -c "import PyQt5; print('PyQt5 OK')"

# Test PipeWire
pw-dump > /dev/null && echo "PipeWire OK"

# Test GUI (will open window)
cd ~/CLionProjects/pipewire-audio-config
python3 pipewire-device-config.py
```

---

## Configuration Directories

After setup, these directories are ready for use:

```
~/.local/share/applications/
  └── pipewire-audio-config.desktop   (App menu entry)

~/.config/wireplumber/wireplumber.conf.d/
  └── (Generated device configs saved here)

~/CLionProjects/pipewire-audio-config/
  ├── pipewire-device-config.py       (Main GUI)
  ├── babyface_channels.py            (Channel maps)
  ├── run-pipewire-config.sh          (Launcher)
  ├── setup.sh                        (Setup script)
  ├── README.md                       (Overview)
  ├── docs/                           (Documentation folder)
  │   ├── SETUP.md                    (This file)
  │   └── ...                         (Other guides)
  └── ...
```

---

## Getting Help

### Command Line Help

```bash
./setup.sh --help
```

### Documentation Files

- **[README.md](../README.md)** - Overview and features
- **[SETUP.md](SETUP.md)** - This file
- **[BUFFER_SIZE_REFERENCE.md](BUFFER_SIZE_REFERENCE.md)** - Buffer size explanation
- **[CHANNEL_LAYOUT.md](CHANNEL_LAYOUT.md)** - Channel layout information
- **[BABYFACE_PRO_CHANNELS.md](BABYFACE_PRO_CHANNELS.md)** - Babyface Pro specific info
- **[DEVICE_DETECTION.md](DEVICE_DETECTION.md)** - Device detection explained
- **[ACP_MODE_EXPLAINED.md](ACP_MODE_EXPLAINED.md)** - ACP mode details

### Reporting Issues

If setup fails, please note:
- Your Linux distribution and version
- Output of: `cat /etc/os-release`
- Output of: `./setup.sh --help`
- Error messages from running `./setup.sh`

---

## System Requirements

### Minimum
- **Linux** with systemd
- **Python 3.6+**
- **PyQt5**
- Package manager (apt, dnf, or pacman) or pip3

### Recommended
- **PipeWire** audio server
- **WirePlumber** session manager
- **Sudo** access for package installation

### Optional but Beneficial
- Desktop environment with application menu
- PipeWire/WirePlumber knowledge helpful for advanced configs

---

## What if Setup Doesn't Work?

### Check System

```bash
# Check OS detection
cat /etc/os-release

# Check package manager
which apt dnf pacman pip3

# Check Python
python3 --version

# Check PyQt5
python3 -c "import PyQt5; print('PyQt5:', PyQt5.__version__)"

# Check PipeWire
which pw-dump
pw-dump --version
```

### Run Verbose Tests

```bash
cd ~/CLionProjects/pipewire-audio-config
bash -x ./setup.sh 2>&1 | tee setup.log
```

This creates `setup.log` with all script operations.

### Manual Fallback

If setup completely fails, follow "Manual Installation" section above.

---

## After Installation

1. Launch the application from your app menu or terminal
2. Select your audio device from the list
3. Adjust channels, sample rate, and buffer size as needed
4. Click "Save as Profile"
5. Follow the instructions to restart WirePlumber:
   ```bash
   systemctl --user restart wireplumber
   ```
6. Your new configuration is now active

---

## Support

For help and troubleshooting:
- See documentation files in project directory
- Run `./setup.sh --help`
- Check system information with commands above
- Verify PipeWire is running: `systemctl --user status wireplumber`
