#!/usr/bin/env python3
"""
PipeWire Audio Device Configuration GUI
Configure USB audio devices: channels, sample rate, latency
Works with any USB audio device on PipeWire
Supports custom channel naming for specific devices
"""

import sys
import json
import subprocess
import re
import time
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QSlider, QPushButton, QGroupBox,
    QMessageBox, QListWidget, QListWidgetItem, QScrollArea, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont


# Device-specific channel mappings
DEVICE_CHANNEL_NAMES = {
    "Babyface Pro": {
        "name": "RME Babyface Pro - Physical I/O",
        "channels": 12,
        "description": "Babyface Pro with main analog I/O + 8x ADAT + S/PDIF",
        "layout": {
            "outputs": [
                "Main-L",      # 0: Analog Out Left (XLR)
                "Main-R",      # 1: Analog Out Right (XLR)
                "ADAT-1",      # 2-9: ADAT Out 1-8
                "ADAT-2",
                "ADAT-3",
                "ADAT-4",
                "ADAT-5",
                "ADAT-6",
                "ADAT-7",
                "ADAT-8",
                "S/PDIF-L",    # 10: Digital Out Left
                "S/PDIF-R",    # 11: Digital Out Right
            ],
            "inputs": [
                "Main-L",      # 0: Analog In Left (XLR)
                "Main-R",      # 1: Analog In Right (XLR)
                "ADAT-1",      # 2-9: ADAT In 1-8
                "ADAT-2",
                "ADAT-3",
                "ADAT-4",
                "ADAT-5",
                "ADAT-6",
                "ADAT-7",
                "ADAT-8",
                "S/PDIF-L",    # 10: Digital In Left
                "S/PDIF-R",    # 11: Digital In Right
            ]
        }
    }
}


class DeviceDetector(QThread):
    """Background thread to detect PipeWire audio devices"""
    devices_found = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            result = subprocess.run(
                ['pw-dump'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                self.error.emit("Failed to get PipeWire devices")
                return

            devices = self._parse_devices(result.stdout)
            self.devices_found.emit(devices)
        except FileNotFoundError:
            self.error.emit("PipeWire not installed or pw-dump not found")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")

    def _parse_devices(self, pw_dump_output):
        """Parse pw-dump JSON output to extract audio devices"""
        devices = []
        try:
            data = json.loads(pw_dump_output)
            
            # Get PipeWire core default sample rate
            default_rate = 48000
            for obj in data:
                if obj.get('type') == 'PipeWire:Interface:Core':
                    props = obj.get('info', {}).get('props', {})
                    # Try to get default clock rate
                    core_rate = props.get('default.clock.rate')
                    if core_rate:
                        try:
                            default_rate = int(core_rate)
                        except (ValueError, TypeError):
                            default_rate = 48000
            
            for obj in data:
                if obj.get('type') == 'PipeWire:Interface:Node' and obj.get('version') == 3:
                    props = obj.get('info', {}).get('props', {})
                    
                    # Only include ALSA audio devices
                    if 'alsa' not in props.get('node.name', ''):
                        continue
                    
                    media_class = props.get('media.class', '')
                    if media_class not in ['Audio/Sink', 'Audio/Source']:
                        continue

                    # Use device rate if set, otherwise use PipeWire default
                    device_rate = props.get('audio.rate', 0)
                    if device_rate == 0:
                        device_rate = default_rate

                    device = {
                        'id': obj.get('id'),
                        'name': props.get('node.name', 'Unknown'),
                        'description': props.get('node.description', 'Unknown'),
                        'media_class': media_class,
                        'channels': props.get('audio.channels', 0),
                        'rate': device_rate,
                        'alsa_path': props.get('api.alsa.path', ''),
                        'use_acp': props.get('api.alsa.use-acp', False),
                        'position': props.get('audio.position', []),
                        'latency_ns': props.get('latency.internal.ns', 0),
                    }
                    devices.append(device)
        except json.JSONDecodeError:
            pass
        
        return devices


class PipeWireConfigGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.devices = []
        self.current_device = None
        self.config_dir = Path.home() / '.config' / 'wireplumber' / 'wireplumber.conf.d'
        self.is_restarting = False  # Prevent multiple restart attempts
        self.ignore_buffer_changes = False  # Ignore buffer size changes during restart
        
        self.init_ui()
        self.load_devices()

    def init_ui(self):
        """Initialize the GUI with tabs"""
        self.setWindowTitle('PipeWire Audio Device Configuration')
        self.setGeometry(100, 100, 1200, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # Device selection and info at top (common)
        device_group = QGroupBox("Audio Devices")
        device_layout = QHBoxLayout()
        
        device_layout.addWidget(QLabel("Select Device:"))
        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        device_layout.addWidget(self.device_combo)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_devices)
        device_layout.addWidget(refresh_btn)
        
        device_group.setLayout(device_layout)
        main_layout.addWidget(device_group)

        # Device info
        info_group = QGroupBox("Device Information")
        info_layout = QVBoxLayout()
        
        self.info_label = QLabel()
        self.info_label.setFont(QFont("Monospace", 9))
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # Tabs for different control panels
        self.tabs = QTabWidget()
        
        # Tab 1: Configuration
        config_tab = QWidget()
        config_layout = QVBoxLayout()
        
        config_group = QGroupBox("Device Configuration")
        config_group_layout = QVBoxLayout()

        # Channels
        channels_layout = QHBoxLayout()
        channels_layout.addWidget(QLabel("Channels:"))
        self.channels_label = QLabel()
        self.channels_label.setStyleSheet("padding: 4px;")
        channels_layout.addWidget(self.channels_label)
        channels_layout.addStretch()
        config_group_layout.addLayout(channels_layout)

        # Sample Rate
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Sample Rate (Hz):"))
        self.rate_combo = QComboBox()
        self.rate_combo.addItems(['44100', '48000', '88200', '96000', '176400', '192000'])
        rate_layout.addWidget(self.rate_combo)
        rate_layout.addStretch()
        config_group_layout.addLayout(rate_layout)

        # Latency (buffer size in samples)
        latency_layout = QHBoxLayout()
        latency_layout.addWidget(QLabel("Buffer Size (samples):"))
        self.latency_combo = QComboBox()
        self.latency_combo.addItems(['32', '64', '128', '256', '512', '1024', '2048', '4096'])
        self.latency_combo.setCurrentText('256')
        self.latency_combo.setToolTip("Smaller = lower latency but more CPU load\nLarger = higher latency but more stable\n\nNote: Changes require WirePlumber restart")
        latency_layout.addWidget(self.latency_combo)
        latency_layout.addStretch()
        config_group_layout.addLayout(latency_layout)

        # ACP Mode toggle
        acp_layout = QHBoxLayout()
        acp_layout.addWidget(QLabel("ACP Mode (limits to stereo):"))
        self.acp_combo = QComboBox()
        self.acp_combo.addItems(['Disabled (Full Channels)', 'Enabled (Stereo Only)'])
        acp_layout.addWidget(self.acp_combo)
        acp_layout.addStretch()
        config_group_layout.addLayout(acp_layout)
        
        config_group.setLayout(config_group_layout)
        config_layout.addWidget(config_group)
        
        # Master Volume & Mute
        volume_group = QGroupBox("Volume & Mute")
        volume_layout = QVBoxLayout()

        master_layout = QHBoxLayout()
        master_layout.addWidget(QLabel("Master Volume:"))
        self.master_volume_slider = QSlider(Qt.Horizontal)
        self.master_volume_slider.setRange(0, 100)
        self.master_volume_slider.setValue(100)
        self.master_volume_slider.setTickPosition(QSlider.TicksBelow)
        self.master_volume_slider.setTickInterval(10)
        master_layout.addWidget(self.master_volume_slider)
        
        self.master_volume_label = QLabel("100%")
        self.master_volume_label.setMinimumWidth(40)
        master_layout.addWidget(self.master_volume_label)
        
        self.master_mute_btn = QPushButton("🔊 Unmuted")
        self.master_mute_btn.setCheckable(True)
        self.master_mute_btn.setMaximumWidth(120)
        self.master_mute_btn.clicked.connect(self.toggle_master_mute)
        master_layout.addWidget(self.master_mute_btn)
        
        volume_layout.addLayout(master_layout)
        volume_group.setLayout(volume_layout)
        config_layout.addWidget(volume_group)
        
        config_layout.addStretch()
        config_tab.setLayout(config_layout)
        self.tabs.addTab(config_tab, "Configuration")

        # Tab 2: Input Levels (ADAT + S/PDIF)
        input_tab = QWidget()
        input_tab_layout = QVBoxLayout()
        
        # Input mute button section
        input_mute_layout = QHBoxLayout()
        self.input_mute_btn = QPushButton("🔊 Mute All Inputs")
        self.input_mute_btn.setCheckable(True)
        self.input_mute_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        self.input_mute_btn.setMaximumWidth(200)
        self.input_mute_btn.clicked.connect(self.on_input_mute_toggled)
        input_mute_layout.addWidget(self.input_mute_btn)
        input_mute_layout.addStretch()
        input_tab_layout.addLayout(input_mute_layout)
        
        # Create sliders for S/PDIF-L (AS1) and S/PDIF-R (AS2) with L/R channels
        self.spdif_sliders = {}  # Key: "Line-AS1-AN1" format, etc
        self.spdif_labels = {}
        self.adat_sliders = {}  # Key: "Line-ADAT3-AN1" format
        self.adat_labels = {}
        self.input_mute_controls = {}  # Track mute state
        
        # Helper function to create a fader column
        def create_fader_column(label_text, control_key, sliders_dict, labels_dict):
            """Create a vertical fader with label and percentage"""
            column = QVBoxLayout()
            column.setSpacing(2)
            
            # Label at top
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-weight: bold; font-size: 11px;")
            column.addWidget(label)
            
            # Fader
            slider = QSlider(Qt.Vertical)
            slider.setRange(0, 65536)
            slider.setValue(65536)
            slider.setTickPosition(QSlider.TicksLeft)
            slider.setTickInterval(6553)
            slider.setMinimumHeight(100)
            slider.setMaximumWidth(30)
            slider.valueChanged.connect(lambda value, key=control_key: self.on_input_gain_changed(key, value))
            column.addWidget(slider, alignment=Qt.AlignCenter)
            
            # Percentage label
            pct_label = QLabel("100%")
            pct_label.setAlignment(Qt.AlignCenter)
            pct_label.setStyleSheet("font-size: 10px;")
            column.addWidget(pct_label)
            
            # Mute button
            mute_btn = QPushButton("M")
            mute_btn.setCheckable(True)
            mute_btn.setMaximumWidth(30)
            mute_btn.setMaximumHeight(25)
            mute_btn.setStyleSheet("font-size: 9px; font-weight: bold;")
            mute_btn.setToolTip(f"Mute {label_text}")
            mute_btn.clicked.connect(lambda checked, key=control_key, sl=slider: self.on_fader_mute_toggled(key, checked, sl))
            column.addWidget(mute_btn, alignment=Qt.AlignCenter)
            
            sliders_dict[control_key] = slider
            labels_dict[control_key] = pct_label
            
            return column
        
        # Create scroll area for horizontal fader layout
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create widget to hold all faders horizontally
        faders_container = QWidget()
        input_group_layout = QHBoxLayout()
        input_group_layout.setContentsMargins(10, 10, 10, 10)
        input_group_layout.setSpacing(25)
        
        # S/PDIF-L (AS1)
        input_group_layout.addLayout(create_fader_column("AS1-L", "Line-AS1-AN1", self.spdif_sliders, self.spdif_labels))
        input_group_layout.addLayout(create_fader_column("AS1-R", "Line-AS1-AN2", self.spdif_sliders, self.spdif_labels))
        
        # S/PDIF-R (AS2)
        input_group_layout.addLayout(create_fader_column("AS2-L", "Line-AS2-AN1", self.spdif_sliders, self.spdif_labels))
        input_group_layout.addLayout(create_fader_column("AS2-R", "Line-AS2-AN2", self.spdif_sliders, self.spdif_labels))
        
        # ADAT Inputs (ADAT-1 to ADAT-6)
        for i in range(1, 7):
            adat_num = i + 2  # ADAT-1 is Line-ADAT3, etc
            
            # Left channel
            input_group_layout.addLayout(create_fader_column(
                f"A{i}L",
                f"Line-ADAT{adat_num}-AN1",
                self.adat_sliders,
                self.adat_labels
            ))
            
            # Right channel
            input_group_layout.addLayout(create_fader_column(
                f"A{i}R",
                f"Line-ADAT{adat_num}-AN2",
                self.adat_sliders,
                self.adat_labels
            ))
        
        input_group_layout.addStretch()
        faders_container.setLayout(input_group_layout)
        scroll_area.setWidget(faders_container)
        
        input_tab_layout.addWidget(scroll_area)
        input_tab.setLayout(input_tab_layout)
        self.tabs.addTab(input_tab, "Input Levels")

        main_layout.addWidget(self.tabs)
        
        # Connect master volume slider
        self.master_volume_slider.valueChanged.connect(self.on_master_volume_changed)
        
        # Connect buffer size combo for immediate config update
        self.latency_combo.currentTextChanged.connect(self.on_buffer_size_changed)
        self.rate_combo.currentTextChanged.connect(self.on_sample_rate_changed)

        # Buttons at bottom
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply Configuration")
        apply_btn.clicked.connect(self.apply_config)
        button_layout.addWidget(apply_btn)
        
        save_btn = QPushButton("Save as Profile")
        save_btn.clicked.connect(self.save_profile)
        button_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_device)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        self.restart_btn = QPushButton("Restart WirePlumber")
        self.restart_btn.setStyleSheet("background-color: #fff3cd; font-weight: bold;")
        self.restart_btn.clicked.connect(self.restart_wireplumber)
        button_layout.addWidget(self.restart_btn)
        
        main_layout.addLayout(button_layout)

        central_widget.setLayout(main_layout)

    def load_devices(self):
        """Load audio devices in background"""
        self.device_combo.clear()
        self.device_combo.addItem("Scanning devices...")
        self.detector = DeviceDetector()
        self.detector.devices_found.connect(self.on_devices_loaded)
        self.detector.error.connect(self.on_detector_error)
        self.detector.start()

    def on_devices_loaded(self, devices):
        """Handle devices loaded from detector"""
        self.devices = devices
        self.device_combo.clear()
        
        if not devices:
            self.device_combo.addItem("No audio devices found")
            return
        
        for device in devices:
            icon = "🔊" if device['media_class'] == 'Audio/Sink' else "🎤"
            label = f"{icon} {device['description']}"
            self.device_combo.addItem(label, device)

    def on_detector_error(self, error):
        """Handle detector error"""
        self.device_combo.clear()
        self.device_combo.addItem(f"Error: {error}")
        QMessageBox.critical(self, "Error", error)

    def on_device_changed(self, index):
        """Handle device selection change"""
        if index < 0 or not self.devices:
            # Clearing device selection, disable volume controls
            self.current_device = None
            # Disconnect volume/mute signals temporarily
            self.master_volume_slider.blockSignals(True)
            self.master_mute_btn.blockSignals(True)
            return
        
        self.current_device = self.device_combo.itemData(index)
        self.update_device_info()
        
        # Re-enable signals after update
        self.master_volume_slider.blockSignals(False)
        self.master_mute_btn.blockSignals(False)

    def _nearest_buffer_size(self, samples):
        """Find nearest standard buffer size"""
        sizes = [32, 64, 128, 256, 512, 1024, 2048, 4096]
        nearest = min(sizes, key=lambda x: abs(x - samples))
        return nearest

    def update_device_info(self):
        """Update device information display"""
        if not self.current_device:
            return
        
        dev = self.current_device
        # Convert nanoseconds to samples using actual device sample rate
        if dev['latency_ns'] > 0 and dev['rate'] > 0:
            latency_ms = dev['latency_ns'] / 1e6
            latency_samples = int((latency_ms * dev['rate']) / 1000)
        else:
            latency_samples = 256
        
        # Find nearest power of 2
        nearest_buffer = self._nearest_buffer_size(latency_samples)
        
        # Check for custom channel names for display
        direction = 'outputs' if dev['media_class'] == 'Audio/Sink' else 'inputs'
        custom_names = self._get_device_channel_names(dev['description'], direction)
        
        # Display channel layout or custom names
        if custom_names and len(custom_names) == dev['channels']:
            channel_info = f"Channel Mapping: {', '.join(custom_names)}"
        else:
            channel_info = f"Channel Layout: {', '.join(dev['position']) if dev['position'] else 'Not specified'}"
        
        info_text = f"""
Device: {dev['description']}
Type: {'Output (Speaker/Headphone)' if dev['media_class'] == 'Audio/Sink' else 'Input (Microphone)'}

Current Settings:
  Channels: {dev['channels']}
  Sample Rate: {dev['rate']} Hz
  ALSA Path: {dev['alsa_path']}
  ACP Mode: {'Enabled' if dev['use_acp'] else 'Disabled'}
  Buffer Size: ~{nearest_buffer} samples ({nearest_buffer / dev['rate'] * 1000:.2f}ms @ {dev['rate']}Hz)
  
{channel_info}
        """
        self.info_label.setText(info_text.strip())
        
        # Update controls
        self.channels_label.setText(str(dev['channels']))
        if dev['rate'] > 0:
            self.rate_combo.setCurrentText(str(dev['rate']))
        self.acp_combo.setCurrentIndex(1 if dev['use_acp'] else 0)

        # Disable ACP mode toggle for Babyface Pro
        if "Babyface" in dev["description"]:
            self.acp_combo.setEnabled(False)
            self.acp_combo.setToolTip("ACP mode managed by 51-rme-babyface.conf - changes do not persist")
        else:
            self.acp_combo.setEnabled(True)
            self.acp_combo.setToolTip("")
        # Block buffer size signal during update to prevent triggering save
        self.latency_combo.blockSignals(True)
        self.latency_combo.setCurrentText(str(nearest_buffer))
        self.latency_combo.blockSignals(False)
        
        # Master volume only (per-channel control not supported in wpctl)

    def apply_config(self):
        """Apply configuration changes"""
        if not self.current_device:
            QMessageBox.warning(self, "Warning", "No device selected")
            return
        
        channels = int(self.channels_label.text())
        sample_rate = int(self.rate_combo.currentText())
        use_acp = self.acp_combo.currentIndex() == 1
        buffer_size = int(self.latency_combo.currentText())
        latency_ms = buffer_size / sample_rate * 1000
        
        QMessageBox.information(
            self, "Configuration Changes",
            f"Applied to: {self.current_device['description']}\n\n"
            f"Channels: {channels}\n"
            f"Sample Rate: {sample_rate} Hz\n"
            f"Buffer Size: {buffer_size} samples ({latency_ms:.2f}ms)\n"
            f"ACP Mode: {'Enabled' if use_acp else 'Disabled'}\n\n"
            f"IMPORTANT - Buffer Size Changes:\n"
            f"To apply buffer size changes, restart WirePlumber:\n\n"
            f"  systemctl --user restart wireplumber\n\n"
            f"Or use 'Save as Profile' then restart PipeWire.\n"
            f"Volume changes take effect immediately."
        )

    def save_profile(self):
        """Save configuration as WirePlumber profile"""
        if not self.current_device:
            QMessageBox.warning(self, "Warning", "No device selected")
            return
        
        channels = int(self.channels_label.text())
        sample_rate = int(self.rate_combo.currentText())
        use_acp = self.acp_combo.currentIndex() == 1
        buffer_size = int(self.latency_combo.currentText())
        latency_ns = int(buffer_size / sample_rate * 1e9)  # Convert to nanoseconds
        
        # Generate device matching pattern
        dev_name = self.current_device['name']
        # Extract USB pattern from device name
        if 'usb' in dev_name:
            # Match USB devices with similar pattern
            match_pattern = dev_name.split('.')[-2]  # Get the unique part
            device_pattern = f'~alsa_.*{match_pattern}.*'
        else:
            device_pattern = f'~alsa_.*{dev_name}.*'
        
        # Build channel position list
        position_map = {
            2: '[ "FL", "FR" ]',
            4: '[ "FL", "FR", "RL", "RR" ]',
            6: '[ "FL", "FR", "FC", "LFE", "RL", "RR" ]',
            8: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "SL", "SR" ]',
            12: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "FLC", "FRC", "RC", "SL", "SR", "TC" ]',
            16: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "FLC", "FRC", "RC", "SL", "SR", "TC", "TFL", "TFR", "TRL", "TRR" ]',
        }
        
        position = position_map.get(channels, '[ "FL", "FR" ]')
        
        # Create config file content with volume/mute info
        config_content = f"""# PipeWire Audio Device Configuration
# Device: {self.current_device['description']}
# Auto-generated configuration
# Buffer Size: {buffer_size} samples ({buffer_size/sample_rate*1000:.2f}ms @ {sample_rate}Hz)
# Master Volume: {self.master_volume_slider.value()}%
# Master Mute: {"true" if self.master_mute_btn.isChecked() else "false"}

monitor.alsa.rules = [
  {{
    matches = [
      {{
        node.name = "{device_pattern}"
      }}
    ]
    actions = {{
      update-props = {{
        api.alsa.use-acp = {str(use_acp).lower()}
        audio.channels = {channels}
        audio.position = {position}
        latency.internal.ns = {latency_ns}
        # Volume settings
        # Master volume: 0-100%
        # Master mute: true/false
      }}
    }}
  }}
]
"""
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        device_short = self.current_device['description'].replace(' ', '-')[:20]
        config_file = self.config_dir / f'50-device-{device_short}.conf'
        
        # Write config
        try:
            config_file.write_text(config_content)
            
            # Also create a separate JSON file for volume settings (easier to load)
            import json
            volume_config = {
                'device': self.current_device['description'],
                'master_volume': self.master_volume_slider.value(),
                'master_muted': self.master_mute_btn.isChecked()
            }
            volume_file = self.config_dir / f'volume-{device_short}.json'
            with open(volume_file, 'w') as f:
                json.dump(volume_config, f, indent=2)
            
            QMessageBox.information(
                self, "Profile Saved",
                f"Configuration saved to:\n{config_file}\n\n"
                f"Volume settings saved to:\n{volume_file}\n\n"
                f"IMPORTANT - Buffer Size Changes:\n"
                f"To apply buffer size and other device changes:\n\n"
                f"  systemctl --user restart wireplumber\n\n"
                f"Note: Volume and mute changes take effect immediately."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profile: {str(e)}")

    def reset_device(self):
        """Reset device to default configuration"""
        if not self.current_device:
            QMessageBox.warning(self, "Warning", "No device selected")
            return
        
        reply = QMessageBox.question(
            self, "Reset Device",
            f"Reset {self.current_device['description']} to default?\n\n"
            "This will remove any custom configuration.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset to default values
            self.rate_combo.setCurrentText('48000')
            self.acp_combo.setCurrentIndex(1)  # Enable ACP (stereo)
            self.latency_combo.setCurrentText('256')  # 256 samples default
            
            QMessageBox.information(
                self, "Reset Complete",
                "Device reset to defaults (2ch, 48kHz, 256 buffer).\n\n"
                "Restart WirePlumber for changes to take effect:\n"
                "systemctl --user restart wireplumber"
            )


    def restart_wireplumber(self):
        """Restart WirePlumber service"""
        reply = QMessageBox.question(
            self, "Restart WirePlumber",
            "This will restart the WirePlumber service.\n\n"
            "Audio may temporarily stop and reconnect.\n"
            "This is needed to apply buffer size and device changes.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # Prevent multiple simultaneous restart attempts
        if self.is_restarting:
            QMessageBox.warning(self, "Warning", "WirePlumber restart already in progress...")
            return
        
        self.is_restarting = True
        self.ignore_buffer_changes = True  # Disable buffer size saves during restart
        self.restart_btn.setEnabled(False)  # Disable restart button during restart
        
        try:
            # Restart WirePlumber (no progress message since it blocks)
            result = subprocess.run(
                ['systemctl', '--user', 'restart', 'wireplumber'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Wait for service to fully restart
                time.sleep(2)
                
                QMessageBox.information(
                    self, "Success",
                    "WirePlumber has been restarted successfully!\n\n"
                    "✅ Buffer size changes applied\n"
                    "✅ Device configuration updated\n"
                    "✅ Audio reconnected\n\n"
                    "Refresh the device list to see updated settings."
                )
                
                # Note: Device refresh handled by user - don't auto-refresh to avoid conflicts
                # User can manually click device refresh if needed
                pass
            else:
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to restart WirePlumber:\n\n{result.stderr}"
                )
        except subprocess.TimeoutExpired:
            QMessageBox.critical(
                self, "Error",
                "Restart command timed out.\n\n"
                "Try manually: systemctl --user restart wireplumber"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Failed to restart WirePlumber:\n\n{str(e)}"
            )

        finally:
            # Always reset the restart flag
            self.is_restarting = False
            self.ignore_buffer_changes = False
            self.restart_btn.setEnabled(True)  # Re-enable restart button
        
    def on_buffer_size_changed(self, value):
        """Handle buffer size change - write config immediately"""
        if not self.current_device or self.ignore_buffer_changes:
            return
        
        try:
            # Get current settings
            channels = int(self.channels_label.text())
            sample_rate = int(self.rate_combo.currentText())
            use_acp = self.acp_combo.currentIndex() == 1
            buffer_size = int(value)
            latency_ns = int(buffer_size / sample_rate * 1e9)
            
            # Generate device matching pattern (same logic as save_profile)
            dev_name = self.current_device['name']
            if 'usb' in dev_name:
                match_pattern = dev_name.split('.')[-2]
                device_pattern = f'~alsa_.*{match_pattern}.*'
            else:
                device_pattern = f'~alsa_.*{dev_name}.*'
            
            # Build channel position list (same as save_profile)
            position_map = {
                2: '[ "FL", "FR" ]',
                4: '[ "FL", "FR", "RL", "RR" ]',
                6: '[ "FL", "FR", "FC", "LFE", "RL", "RR" ]',
                8: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "SL", "SR" ]',
                12: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "FLC", "FRC", "RC", "SL", "SR", "TC" ]',
                16: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "FLC", "FRC", "RC", "SL", "SR", "TC", "TFL", "TFR", "TRL", "TRR" ]',
            }
            position = position_map.get(channels, '[ "FL", "FR" ]')
            
            # Create config file (same format as save_profile)
            config_content = f"""# PipeWire Audio Device Configuration
# Device: {self.current_device['description']}
# Auto-generated configuration
# Buffer Size: {buffer_size} samples ({buffer_size/sample_rate*1000:.2f}ms @ {sample_rate}Hz)
# Master Volume: {self.master_volume_slider.value()}%
# Master Mute: {"true" if self.master_mute_btn.isChecked() else "false"}

monitor.alsa.rules = [
  {{
    matches = [
      {{
        node.name = "{device_pattern}"
      }}
    ]
    actions = {{
      update-props = {{
        api.alsa.use-acp = {str(use_acp).lower()}
        audio.channels = {channels}
        audio.position = {position}
        latency.internal.ns = {latency_ns}
        # Volume settings
        # Master volume: 0-100%
        # Master mute: true/false
      }}
    }}
  }}
]
"""
            
            # Save config file to WirePlumber config directory
            device_short = self.current_device['description'].replace(' ', '-')[:20]
            config_file = self.config_dir / f'50-device-{device_short}.conf'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text(config_content)
            
            # Print status messages
            print(f"✅ Buffer size updated to {buffer_size} samples ({buffer_size/sample_rate*1000:.2f}ms)")
            print(f"✅ Config saved to {config_file}")
            print(f"⚠️  Restart WirePlumber to apply changes: systemctl --user restart wireplumber")
            
        except Exception as e:
            print(f"❌ Error updating buffer size: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_device_channel_names(self, device_description, direction='outputs'):
        """Get custom channel names for known devices like Babyface Pro"""
        # Check if this device has custom naming
        for device_key, device_config in DEVICE_CHANNEL_NAMES.items():
            if device_key.lower() in device_description.lower():
                return device_config['layout'].get(direction, [])
        return None

    def on_sample_rate_changed(self, value):
        """Handle sample rate change - save to WirePlumber config"""
        if not self.current_device or self.ignore_buffer_changes:
            return
        
        try:
            # Get current settings
            channels = int(self.channels_label.text())
            sample_rate = int(value)
            use_acp = self.acp_combo.currentIndex() == 1
            buffer_size = int(self.latency_combo.currentText())
            latency_ns = int(buffer_size / sample_rate * 1e9)
            
            # Generate device matching pattern
            dev_name = self.current_device['name']
            if 'usb' in dev_name:
                match_pattern = dev_name.split('.')[-2]
                device_pattern = f'~alsa_.*{match_pattern}.*'
            else:
                device_pattern = f'~alsa_.*{dev_name}.*'
            
            # Build channel position list
            position_map = {
                2: '[ "FL", "FR" ]',
                4: '[ "FL", "FR", "RL", "RR" ]',
                6: '[ "FL", "FR", "FC", "LFE", "RL", "RR" ]',
                8: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "SL", "SR" ]',
                12: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "FLC", "FRC", "RC", "SL", "SR", "TC" ]',
                16: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "FLC", "FRC", "RC", "SL", "SR", "TC", "TFL", "TFR", "TRL", "TRR" ]',
            }
            position = position_map.get(channels, '[ "FL", "FR" ]')
            
            # Create config file with updated sample rate
            config_content = f"""# PipeWire Audio Device Configuration
# Device: {self.current_device['description']}
# Auto-generated configuration
# Sample Rate: {sample_rate} Hz
# Buffer Size: {buffer_size} samples ({buffer_size/sample_rate*1000:.2f}ms @ {sample_rate}Hz)
# Master Volume: {self.master_volume_slider.value()}%
# Master Mute: {"true" if self.master_mute_btn.isChecked() else "false"}

monitor.alsa.rules = [
  {{
    matches = [
      {{
        node.name = "{device_pattern}"
      }}
    ]
    actions = {{
      update-props = {{
        api.alsa.use-acp = {str(use_acp).lower()}
        audio.channels = {channels}
        audio.position = {position}
        audio.rate = {sample_rate}
        latency.internal.ns = {latency_ns}
        # Volume settings
        # Master volume: 0-100%
        # Master mute: true/false
      }}
    }}
  }}
]
"""
            
            # Save config file
            device_short = self.current_device['description'].replace(' ', '-')[:20]
            config_file = self.config_dir / f'50-device-{device_short}.conf'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text(config_content)
            
            # Print status
            print(f"✅ Sample rate updated to {sample_rate} Hz")
            print(f"✅ Config saved to {config_file}")
            print(f"⚠️  Restart WirePlumber to apply changes: systemctl --user restart wireplumber")
            
        except Exception as e:
            print(f"❌ Error updating sample rate: {e}")
            import traceback
            traceback.print_exc()

    def on_acp_mode_changed(self, index):
        """Handle ACP mode change - save to WirePlumber config"""
        if not self.current_device or self.ignore_buffer_changes:
            return
        
        try:
            # Get current settings
            channels = int(self.channels_label.text())
            sample_rate = int(self.rate_combo.currentText())
            use_acp = index == 1
            buffer_size = int(self.latency_combo.currentText())
            latency_ns = int(buffer_size / sample_rate * 1e9)
            
            # Generate device matching pattern
            dev_name = self.current_device['name']
            if 'usb' in dev_name:
                match_pattern = dev_name.split('.')[-2]
                device_pattern = f'~alsa_.*{match_pattern}.*'
            else:
                device_pattern = f'~alsa_.*{dev_name}.*'
            
            # Build channel position list
            position_map = {
                2: '[ "FL", "FR" ]',
                4: '[ "FL", "FR", "RL", "RR" ]',
                6: '[ "FL", "FR", "FC", "LFE", "RL", "RR" ]',
                8: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "SL", "SR" ]',
                12: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "FLC", "FRC", "RC", "SL", "SR", "TC" ]',
                16: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "FLC", "FRC", "RC", "SL", "SR", "TC", "TFL", "TFR", "TRL", "TRR" ]',
            }
            position = position_map.get(channels, '[ "FL", "FR" ]')
            
            # Create config file with updated ACP mode
            config_content = f"""# PipeWire Audio Device Configuration
# Device: {self.current_device['description']}
# Auto-generated configuration
# ACP Mode: {'Enabled (Stereo Only)' if use_acp else 'Disabled (Full Channels)'}
# Sample Rate: {sample_rate} Hz
# Buffer Size: {buffer_size} samples ({buffer_size/sample_rate*1000:.2f}ms @ {sample_rate}Hz)
# Master Volume: {self.master_volume_slider.value()}%
# Master Mute: {"true" if self.master_mute_btn.isChecked() else "false"}

monitor.alsa.rules = [
  {{
    matches = [
      {{
        node.name = "{device_pattern}"
      }}
    ]
    actions = {{
      update-props = {{
        api.alsa.use-acp = {str(use_acp).lower()}
        audio.channels = {channels}
        audio.position = {position}
        audio.rate = {sample_rate}
        latency.internal.ns = {latency_ns}
        # Volume settings
        # Master volume: 0-100%
        # Master mute: true/false
      }}
    }}
  }}
]
"""
            
            # Save config file
            device_short = self.current_device['description'].replace(' ', '-')[:20]
            config_file = self.config_dir / f'50-device-{device_short}.conf'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text(config_content)
            
            # Print status
            mode_str = "Enabled (Stereo Only)" if use_acp else "Disabled (Full Channels)"
            print(f"✅ ACP mode changed to: {mode_str}")
            print(f"✅ Config saved to {config_file}")
            print(f"⚠️  Restart WirePlumber to apply changes: systemctl --user restart wireplumber")
            
        except Exception as e:
            print(f"❌ Error updating ACP mode: {e}")
            import traceback
            traceback.print_exc()

    def toggle_master_mute(self, checked):
        """Toggle master mute"""
        if checked:
            self.master_mute_btn.setText("🔇 Muted")
            self.master_mute_btn.setStyleSheet("background-color: #ffcccc;")
        else:
            self.master_mute_btn.setText("🔊 Unmuted")
            self.master_mute_btn.setStyleSheet("")
        
        # Apply mute to PipeWire device
        if self.current_device:
            self._apply_mute_to_device(checked)

    def on_input_mute_toggled(self, checked):
        """Toggle mute for all input faders"""
        if checked:
            self.input_mute_btn.setText("🔇 All Inputs Muted")
            self.input_mute_btn.setStyleSheet("background-color: #ffcccc; font-weight: bold; padding: 8px;")
            # Store current slider values and set to 0
            self.input_mute_controls['muted'] = True
            self.input_mute_controls['stored_values'] = {}
            for key, slider in {**self.spdif_sliders, **self.adat_sliders}.items():
                self.input_mute_controls['stored_values'][key] = slider.value()
                slider.blockSignals(True)
                slider.setValue(0)
                slider.blockSignals(False)
        else:
            self.input_mute_btn.setText("🔊 Mute All Inputs")
            self.input_mute_btn.setStyleSheet("font-weight: bold; padding: 8px;")
            # Restore stored slider values
            self.input_mute_controls['muted'] = False
            if 'stored_values' in self.input_mute_controls:
                for key, value in self.input_mute_controls['stored_values'].items():
                    if key in self.spdif_sliders:
                        self.spdif_sliders[key].blockSignals(True)
                        self.spdif_sliders[key].setValue(value)
                        self.spdif_sliders[key].blockSignals(False)
                    elif key in self.adat_sliders:
                        self.adat_sliders[key].blockSignals(True)
                        self.adat_sliders[key].setValue(value)
                        self.adat_sliders[key].blockSignals(False)

    def on_fader_mute_toggled(self, control_key, checked, slider):
        """Toggle mute for individual fader"""
        print(f"DEBUG: on_fader_mute_toggled called - control_key={control_key}, checked={checked}, slider.value()={slider.value()}")
        if checked:
            # Store current value and set to 0 (mute)
            if 'fader_mutes' not in self.input_mute_controls:
                self.input_mute_controls['fader_mutes'] = {}
            self.input_mute_controls['fader_mutes'][control_key] = slider.value()
            print(f"DEBUG: Storing {control_key} value: {slider.value()}")
            slider.blockSignals(True)
            slider.setValue(0)
            slider.blockSignals(False)
            # Explicitly apply the change to device since we blocked signals
            self._apply_input_gain(control_key, 0)
            print(f"DEBUG: Set {control_key} to 0, new value: {slider.value()}")
        else:
            # Restore stored value
            if 'fader_mutes' in self.input_mute_controls and control_key in self.input_mute_controls['fader_mutes']:
                stored_value = self.input_mute_controls['fader_mutes'][control_key]
                print(f"DEBUG: Restoring {control_key} value: {stored_value}")
                slider.blockSignals(True)
                slider.setValue(stored_value)
                slider.blockSignals(False)
                # Explicitly apply the change to device since we blocked signals
                self._apply_input_gain(control_key, stored_value)
                print(f"DEBUG: Restored {control_key}, new value: {slider.value()}")
            else:
                print(f"DEBUG: No stored value found for {control_key}")

    def on_master_volume_changed(self, value):
        """Handle master volume slider change"""
        self.master_volume_label.setText(f"{value}%")
        
        # Apply volume to PipeWire device
        if self.current_device:
            self._apply_volume_to_device(value)

    def _get_wpctl_device_id(self, device_name):
        """Find the wpctl device ID for a given device name"""
        try:
            result = subprocess.run(
                ['wpctl', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return None
            
            # Parse wpctl status output to find device ID
            # We want sinks/sources, not the device itself
            lines = result.stdout.split('\n')
            sink_id = None
            
            for line in lines:
                # Look for sink line with device name (contains '*' for default)
                if device_name.lower() in line.lower() and '*' in line:
                    # Extract ID using regex: match numbers before the device name
                    # Format: "│  *   67. Device Name [vol: 0.50]"
                    match = re.search(r'\*\s+(\d+)', line)
                    if match:
                        sink_id = int(match.group(1))
                        break
            
            # Fallback: if not found, try to find any matching device ID (without * requirement)
            if sink_id is None:
                for line in lines:
                    if device_name.lower() in line.lower():
                        # Extract any number before device name
                        match = re.search(r'^\s*[│├└]*\s*\*?\s+(\d+)', line)
                        if match:
                            sink_id = int(match.group(1))
                            break
            
            return sink_id
        except Exception as e:
            print(f"Error getting wpctl device ID: {e}")
            return None

    def _apply_mute_to_device(self, mute_state):
        """Apply mute state to the current device using wpctl"""
        try:
            if not self.current_device:
                return
            
            # Get wpctl device ID
            device_id = self._get_wpctl_device_id(self.current_device['description'])
            if device_id is None:
                print(f"Warning: Could not find wpctl ID for {self.current_device['description']}")
                return
            
            # Convert boolean to wpctl mute value (1 = muted, 0 = unmuted)
            mute_value = 1 if mute_state else 0
            
            # Set mute using wpctl
            result = subprocess.run(
                ['wpctl', 'set-mute', str(device_id), str(mute_value)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"Error setting mute: {result.stderr}")
        except Exception as e:
            print(f"Error applying mute: {e}")

    def _apply_volume_to_device(self, volume_percent):
        """Apply volume percentage to the current device using wpctl"""
        try:
            if not self.current_device:
                return
            
            # Get wpctl device ID
            device_id = self._get_wpctl_device_id(self.current_device['description'])
            if device_id is None:
                print(f"Warning: Could not find wpctl ID for {self.current_device['description']}")
                return
            
            # Convert percentage (0-100) to decimal (0.0-1.0)
            volume_decimal = volume_percent / 100.0
            
            # Set volume using wpctl (master/all channels)
            result = subprocess.run(
                ['wpctl', 'set-volume', str(device_id), f'{volume_decimal:.2f}'],
                capture_output=True,
                text=True,
                timeout=5
            )
             
            if result.returncode != 0:
                print(f"Error setting volume: {result.stderr}")
        except Exception as e:
            print(f"Error applying volume: {e}")

    def on_input_gain_changed(self, control_key, value):
        """Handle input gain slider change for any ADAT or S/PDIF input"""
        # Update display label with percentage
        percent = round((value / 65536.0) * 100)
        
        # Update the appropriate label
        if control_key in self.adat_labels:
            self.adat_labels[control_key].setText(f"{percent}%")
        elif control_key in self.spdif_labels:
            self.spdif_labels[control_key].setText(f"{percent}%")
        
        # Apply gain to ALSA device
        self._apply_input_gain(control_key, value)
    
    def _apply_input_gain(self, control_name, value):
        """Apply input gain via ALSA mixer for any ADAT or S/PDIF input"""
        try:
            # control_name is in the format: "Line-ADAT3-AN1", "Line-AS1-AN2", etc.
            # Get ALSA card number (using first USB audio device, typically hw:1)
            # For Babyface Pro, it's usually card 1
            card_number = 1
            
            # Set ALSA mixer control via amixer
            result = subprocess.run(
                ['amixer', '-c', str(card_number), 'sset', control_name, str(value)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"Error setting {control_name}: {result.stderr}")
        except Exception as e:
             print(f"Error applying input gain for {control_name}: {e}")


def main():
    app = QApplication(sys.argv)
    window = PipeWireConfigGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
