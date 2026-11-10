#!/bin/bash
################################################################################
# PipeWire Audio Config - Setup Script
# 
# Automated installation and setup for all supported Linux distributions
# Handles dependency detection, installation, and configuration
#
# Supported Distributions:
#   • Ubuntu/Debian (apt)
#   • Fedora/RHEL (dnf)
#   • Arch Linux (pacman)
#   • MX Linux (apt)
#   • Any systemd-based system with pip3
#
# Usage:
#   ./setup.sh              # Interactive setup
#   ./setup.sh --uninstall  # Uninstall the application
#   ./setup.sh --help       # Show help
################################################################################

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="PipeWire Audio Config"
MAIN_SCRIPT="pipewire-device-config.py"
LAUNCHER_SCRIPT="run-pipewire-config.sh"
DESKTOP_FILE_NAME="pipewire-audio-config.desktop"
DESKTOP_ENTRY_DIR="$HOME/.local/share/applications"
CONFIG_DIR="$HOME/.config/wireplumber/wireplumber.conf.d"

# Detect system info
detect_system() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_NAME="$ID"
        OS_VERSION="$VERSION_ID"
    else
        echo -e "${RED}✗${NC} Cannot detect operating system"
        exit 1
    fi
}

# Detect package manager
detect_package_manager() {
    if command -v apt &> /dev/null; then
        PACKAGE_MANAGER="apt"
        INSTALL_CMD="sudo apt update && sudo apt install -y"
        PYTHON_PKG="python3"
        PYQT5_PKG="python3-pyqt5"
        PIPEWIRE_PKG="pipewire"
        return 0
    elif command -v dnf &> /dev/null; then
        PACKAGE_MANAGER="dnf"
        INSTALL_CMD="sudo dnf install -y"
        PYTHON_PKG="python3"
        PYQT5_PKG="python3-pyqt5"
        PIPEWIRE_PKG="pipewire"
        return 0
    elif command -v pacman &> /dev/null; then
        PACKAGE_MANAGER="pacman"
        INSTALL_CMD="sudo pacman -S --noconfirm"
        PYTHON_PKG="python"
        PYQT5_PKG="python-pyqt5"
        PIPEWIRE_PKG="pipewire"
        return 0
    else
        echo -e "${RED}✗${NC} No supported package manager found"
        echo "   Supported: apt, dnf, pacman"
        echo "   Falling back to pip3 only installation..."
        PACKAGE_MANAGER="pip3"
        return 0
    fi
}

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║          PipeWire Audio Config - Setup Wizard                  ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print section header
print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

# Print success message
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Print error message
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Print warning message
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Print info message
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check Python version
check_python() {
    print_section "Checking Python Installation"
    
    if command_exists python3; then
        python_version=$(python3 --version 2>&1 | awk '{print $2}')
        major=$(echo "$python_version" | cut -d. -f1)
        minor=$(echo "$python_version" | cut -d. -f2)
        
        if [ "$major" -ge 3 ] && [ "$minor" -ge 6 ]; then
            print_success "Python $python_version found"
            return 0
        else
            print_warning "Python $python_version found (need 3.6+)"
            return 1
        fi
    else
        print_error "Python3 not found"
        return 1
    fi
}

# Check PyQt5
check_pyqt5() {
    print_section "Checking PyQt5 Installation"
    
    if python3 -c "import PyQt5" 2>/dev/null; then
        pyqt5_version=$(python3 -c "import PyQt5; print(PyQt5.QtCore.PYQT_VERSION_STR)" 2>/dev/null || echo "unknown")
        print_success "PyQt5 $pyqt5_version found"
        return 0
    else
        print_warning "PyQt5 not found"
        return 1
    fi
}

# Check PipeWire
check_pipewire() {
    print_section "Checking PipeWire Installation"
    
    if command_exists pw-dump; then
        pw_version=$(pw-dump --version 2>/dev/null | head -n1 || echo "unknown")
        print_success "PipeWire found ($pw_version)"
        return 0
    else
        print_error "PipeWire not found (pw-dump)"
        return 1
    fi
}

# Install Python
install_python() {
    print_section "Installing Python3"
    
    if [ "$PACKAGE_MANAGER" = "pip3" ]; then
        print_warning "No package manager available - Python3 must be installed manually"
        return 1
    fi
    
    echo "Running: $INSTALL_CMD $PYTHON_PKG"
    eval "$INSTALL_CMD $PYTHON_PKG" || {
        print_error "Failed to install Python3"
        return 1
    }
    
    check_python
}

# Install PyQt5
install_pyqt5() {
    print_section "Installing PyQt5"
    
    if [ "$PACKAGE_MANAGER" = "pip3" ]; then
        print_info "Installing PyQt5 via pip3..."
        pip3 install --user PyQt5 || {
            print_error "Failed to install PyQt5 via pip3"
            return 1
        }
    else
        echo "Running: $INSTALL_CMD $PYQT5_PKG"
        eval "$INSTALL_CMD $PYQT5_PKG" || {
            print_error "Failed to install PyQt5"
            return 1
        }
    fi
    
    check_pyqt5
}

# Install PipeWire (optional - may already be running)
install_pipewire() {
    print_section "Checking PipeWire"
    
    if check_pipewire; then
        return 0
    fi
    
    print_warning "PipeWire not found. Install it?"
    read -p "Install PipeWire? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Skipping PipeWire installation"
        return 0
    fi
    
    if [ "$PACKAGE_MANAGER" = "pip3" ]; then
        print_error "Cannot install PipeWire via pip3 - use your package manager"
        return 1
    fi
    
    echo "Running: $INSTALL_CMD $PIPEWIRE_PKG"
    eval "$INSTALL_CMD $PIPEWIRE_PKG" || {
        print_error "Failed to install PipeWire"
        return 1
    }
    
    check_pipewire
}

# Verify main script exists
verify_main_script() {
    print_section "Verifying Installation Files"
    
    if [ ! -f "$SCRIPT_DIR/$MAIN_SCRIPT" ]; then
        print_error "Main script not found: $SCRIPT_DIR/$MAIN_SCRIPT"
        return 1
    fi
    print_success "Found: $MAIN_SCRIPT"
    
    if [ ! -f "$SCRIPT_DIR/$LAUNCHER_SCRIPT" ]; then
        print_error "Launcher script not found: $SCRIPT_DIR/$LAUNCHER_SCRIPT"
        return 1
    fi
    print_success "Found: $LAUNCHER_SCRIPT"
    
    return 0
}

# Make scripts executable
make_executable() {
    print_section "Setting Permissions"
    
    chmod +x "$SCRIPT_DIR/$MAIN_SCRIPT" || {
        print_error "Failed to make $MAIN_SCRIPT executable"
        return 1
    }
    print_success "Made executable: $MAIN_SCRIPT"
    
    chmod +x "$SCRIPT_DIR/$LAUNCHER_SCRIPT" || {
        print_error "Failed to make $LAUNCHER_SCRIPT executable"
        return 1
    }
    print_success "Made executable: $LAUNCHER_SCRIPT"
    
    chmod +x "$SCRIPT_DIR/setup.sh" || {
        print_error "Failed to make setup.sh executable"
        return 1
    }
    print_success "Made executable: setup.sh"
    
    return 0
}

# Create desktop entry
install_desktop_entry() {
    print_section "Installing Desktop Entry"
    
    mkdir -p "$DESKTOP_ENTRY_DIR" || {
        print_error "Failed to create $DESKTOP_ENTRY_DIR"
        return 1
    }
    
    # Check if desktop file already exists
    if [ -f "$DESKTOP_ENTRY_DIR/$DESKTOP_FILE_NAME" ]; then
        print_info "Desktop entry already exists"
    fi
    
    # Create desktop file
    cat > "$DESKTOP_ENTRY_DIR/$DESKTOP_FILE_NAME" << EOF
[Desktop Entry]
Type=Application
Name=PipeWire Audio Config
Comment=Configure audio device channels, sample rate, and buffer size
Exec=$SCRIPT_DIR/$LAUNCHER_SCRIPT
Icon=audio-card
Categories=Utility;AudioVideo;
Terminal=false
StartupNotify=true
EOF
    
    if [ -f "$DESKTOP_ENTRY_DIR/$DESKTOP_FILE_NAME" ]; then
        print_success "Desktop entry installed to: $DESKTOP_ENTRY_DIR/$DESKTOP_FILE_NAME"
        
        # Update desktop database
        if command_exists update-desktop-database; then
            update-desktop-database "$DESKTOP_ENTRY_DIR" 2>/dev/null || true
            print_success "Updated desktop database"
        fi
        
        return 0
    else
        print_error "Failed to create desktop entry"
        return 1
    fi
}

# Create WirePlumber config directory
prepare_config_directory() {
    print_section "Preparing Configuration Directory"
    
    mkdir -p "$CONFIG_DIR" || {
        print_error "Failed to create $CONFIG_DIR"
        return 1
    }
    
    print_success "Configuration directory ready: $CONFIG_DIR"
    return 0
}

# Test GUI launch
test_gui_launch() {
    print_section "Testing GUI Launch"
    
    print_info "Testing module imports..."
    
    if python3 << 'PYEOF'
import sys
sys.path.insert(0, '$SCRIPT_DIR')
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("gui", "$SCRIPT_DIR/$MAIN_SCRIPT")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("✓ GUI module loads successfully")
    sys.exit(0)
except Exception as e:
    print(f"✗ Failed to load GUI module: {e}")
    sys.exit(1)
PYEOF
    then
        return 0
    else
        print_error "Failed to test GUI module"
        return 1
    fi
}

# Run verification tests
run_verification() {
    print_section "Running Verification Tests"
    
    local failed=0
    
    print_info "Test 1: Python version"
    if check_python; then
        print_success "Python OK"
    else
        print_error "Python check failed"
        failed=$((failed + 1))
    fi
    
    print_info "Test 2: PyQt5 installation"
    if check_pyqt5; then
        print_success "PyQt5 OK"
    else
        print_error "PyQt5 check failed"
        failed=$((failed + 1))
    fi
    
    print_info "Test 3: PipeWire installation"
    if check_pipewire; then
        print_success "PipeWire OK"
    else
        print_warning "PipeWire not found (needed for actual use)"
    fi
    
    print_info "Test 4: Main script exists"
    if [ -f "$SCRIPT_DIR/$MAIN_SCRIPT" ]; then
        print_success "Main script OK"
    else
        print_error "Main script missing"
        failed=$((failed + 1))
    fi
    
    print_info "Test 5: Launcher script exists"
    if [ -f "$SCRIPT_DIR/$LAUNCHER_SCRIPT" ]; then
        print_success "Launcher script OK"
    else
        print_error "Launcher script missing"
        failed=$((failed + 1))
    fi
    
    print_info "Test 6: Desktop entry installed"
    if [ -f "$DESKTOP_ENTRY_DIR/$DESKTOP_FILE_NAME" ]; then
        print_success "Desktop entry OK"
    else
        print_warning "Desktop entry not installed"
    fi
    
    return $failed
}

# Print installation summary
print_summary() {
    print_section "Installation Summary"
    
    echo ""
    echo "Project Location: $SCRIPT_DIR"
    echo "Desktop Entry: $DESKTOP_ENTRY_DIR/$DESKTOP_FILE_NAME"
    echo "Config Directory: $CONFIG_DIR"
    echo ""
    
    echo -e "${GREEN}Installation Complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Launch from application menu: ${BLUE}PipeWire Audio Config${NC}"
    echo "  2. Or run manually: ${BLUE}$SCRIPT_DIR/$LAUNCHER_SCRIPT${NC}"
    echo "  3. Select your audio device and configure settings"
    echo "  4. Save configuration"
    echo "  5. Restart WirePlumber: ${BLUE}systemctl --user restart wireplumber${NC}"
    echo ""
    echo "For help, see: $SCRIPT_DIR/README.md"
    echo ""
}

# Uninstall function
uninstall() {
    print_banner
    print_section "Uninstalling $PROJECT_NAME"
    
    read -p "This will uninstall $PROJECT_NAME. Continue? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Uninstall cancelled"
        return 0
    fi
    
    print_info "Removing desktop entry..."
    if [ -f "$DESKTOP_ENTRY_DIR/$DESKTOP_FILE_NAME" ]; then
        rm -f "$DESKTOP_ENTRY_DIR/$DESKTOP_FILE_NAME"
        print_success "Removed: $DESKTOP_FILE_NAME"
        
        if command_exists update-desktop-database; then
            update-desktop-database "$DESKTOP_ENTRY_DIR" 2>/dev/null || true
        fi
    fi
    
    print_warning "NOT removing configuration files (preserve user configs)"
    print_info "Config directory: $CONFIG_DIR"
    
    echo ""
    print_success "Uninstall complete"
    echo ""
    echo "To completely remove the application:"
    echo "  rm -rf $SCRIPT_DIR"
    echo ""
}

# Print help
print_help() {
    cat << EOF
${BLUE}PipeWire Audio Config - Setup Script${NC}

Usage:
  ./setup.sh              Interactive setup and installation
  ./setup.sh --uninstall  Uninstall the application
  ./setup.sh --help       Show this help message

Environment Variables:
  No configuration needed - script auto-detects system

Installation includes:
  • Dependency detection and installation (Python3, PyQt5, PipeWire)
  • Permission configuration for scripts
  • Desktop menu entry setup
  • Configuration directory creation
  • Installation verification tests

Supported Distributions:
  • Ubuntu / Debian (apt)
  • Fedora / RHEL / CentOS (dnf)
  • Arch Linux (pacman)
  • MX Linux (apt-based)
  • Any systemd system (pip3 fallback)

After Installation:
  1. Launch from your application menu
  2. Select an audio device
  3. Configure channels, sample rate, and buffer size
  4. Save configuration
  5. Restart WirePlumber for changes to take effect

For more information, see:
  • README.md - Overview and features
  • docs/SETUP.md - Detailed setup guide
  • docs/BUFFER_SIZE_REFERENCE.md - Buffer size explained

EOF
}

# Main installation flow
main() {
    print_banner
    
    # Parse arguments
    if [ $# -gt 0 ]; then
        case "$1" in
            --uninstall)
                uninstall
                exit 0
                ;;
            --help|-h)
                print_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                print_help
                exit 1
                ;;
        esac
    fi
    
    # Detect system
    print_section "Detecting System"
    detect_system
    detect_package_manager
    print_success "Detected: $OS_NAME (Package manager: $PACKAGE_MANAGER)"
    
    # Check dependencies
    print_section "Checking Dependencies"
    
    python_ok=0
    pyqt5_ok=0
    pipewire_ok=0
    
    check_python || python_ok=1
    check_pyqt5 || pyqt5_ok=1
    check_pipewire || pipewire_ok=1
    
    # Install missing dependencies
    if [ $python_ok -ne 0 ]; then
        install_python || exit 1
    fi
    
    if [ $pyqt5_ok -ne 0 ]; then
        install_pyqt5 || exit 1
    fi
    
    install_pipewire || {
        print_warning "PipeWire installation recommended but not critical"
    }
    
    # Verify installation files
    verify_main_script || exit 1
    
    # Setup application
    make_executable || exit 1
    prepare_config_directory || exit 1
    install_desktop_entry || exit 1
    
    # Run tests
    if run_verification; then
        echo ""
        print_success "All verification tests passed!"
    else
        print_warning "Some verification tests failed - installation may need attention"
    fi
    
    # Print summary
    echo ""
    print_summary
}

# Run main if script is executed (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
