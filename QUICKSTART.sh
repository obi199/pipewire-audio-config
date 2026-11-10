#!/bin/bash
# Quick Start Guide for PipeWire Audio Device Configuration

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     PipeWire Audio Device Configuration GUI                   ║"
echo "║     Location: /home/pete/CLionProjects/pipewire-audio-config   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

PROJECT_DIR="/home/pete/CLionProjects/pipewire-audio-config"

# Check if we're in the right directory
if [ ! -f "$PROJECT_DIR/pipewire-device-config.py" ]; then
    echo "❌ Error: Project files not found at $PROJECT_DIR"
    exit 1
fi

echo "📁 Project Location:"
echo "   $PROJECT_DIR"
echo ""

echo "📋 Project Files:"
ls -1 "$PROJECT_DIR" | grep -E "\.(py|sh|md|txt|gitignore|LICENSE)$" | while read file; do
    echo "   ✓ $file"
done
echo ""

echo "🚀 How to Run:"
echo ""
echo "   Option 1: Using launcher script"
echo "   $ cd $PROJECT_DIR"
echo "   $ ./run-pipewire-config.sh"
echo ""
echo "   Option 2: Direct Python"
echo "   $ python3 $PROJECT_DIR/pipewire-device-config.py"
echo ""
echo "   Option 3: From anywhere (add to PATH)"
echo "   $ export PATH=\"$PROJECT_DIR:\$PATH\""
echo "   $ python3 pipewire-device-config.py"
echo ""

echo "📦 Dependencies:"
echo "   • Python 3.6+"
echo "   • PyQt5"
echo "   • PipeWire (must be running)"
echo ""

echo "💾 Install Dependencies:"
echo "   Ubuntu/Debian:"
echo "   $ sudo apt install python3 python3-pyqt5"
echo ""
echo "   Fedora:"
echo "   $ sudo dnf install python3 python3-qt5"
echo ""
echo "   Arch:"
echo "   $ sudo pacman -S python python-pyqt5"
echo ""

echo "📖 Documentation:"
echo "   • README.md - Main documentation"
echo "   • docs/PIPEWIRE_CONFIG_README.md - Detailed guide"
echo "   • docs/BUFFER_SIZE_REFERENCE.md - Buffer size reference"
echo "   • docs/SETUP.md - Setup guide"
echo ""

echo "🔧 After Configuration:"
echo "   1. Open the GUI app"
echo "   2. Select your audio device"
echo "   3. Configure channels, sample rate, buffer size"
echo "   4. Click 'Save as Profile'"
echo "   5. Restart WirePlumber:"
echo "   $ systemctl --user restart wireplumber"
echo ""

echo "📂 Configuration files saved to:"
echo "   ~/.config/wireplumber/wireplumber.conf.d/"
echo ""

echo "🎯 For RME Babyface Pro:"
echo "   • Channels: 12"
echo "   • Sample Rate: 48000 or 96000 Hz"
echo "   • Buffer Size: 128-256 samples"
echo "   • ACP Mode: Disabled"
echo ""

echo "✨ Ready to use!"
echo ""
