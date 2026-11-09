#!/bin/bash
# PipeWire Audio Device Configuration GUI
# Simple configuration tool for audio devices on PipeWire

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if PipeWire is running
if ! pgrep -x pipewire > /dev/null; then
    echo "⚠ Error: PipeWire is not running"
    echo "Start it with: systemctl --user start pipewire"
    exit 1
fi

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "⚠ Error: Python3 is required"
    exit 1
fi

# Check PyQt5
if ! python3 -c "import PyQt5" 2>/dev/null; then
    echo "⚠ Error: PyQt5 is not installed"
    echo ""
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt install python3-pyqt5"
    echo "  Fedora: sudo dnf install python3-qt5"
    echo "  Arch: sudo pacman -S python-pyqt5"
    exit 1
fi

# Run the GUI
echo "Starting PipeWire Audio Device Configuration..."
python3 "$SCRIPT_DIR/pipewire-device-config.py"
