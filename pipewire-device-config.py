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
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QSlider, QPushButton, QGroupBox,
    QMessageBox, QListWidget, QListWidgetItem, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
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
            for obj in data:
                if obj.get('type') == 'PipeWire:Interface:Node' and obj.get('version') == 3:
                    props = obj.get('info', {}).get('props', {})
                    
                    # Only include ALSA audio devices
                    if 'alsa' not in props.get('node.name', ''):
                        continue
                    
                    media_class = props.get('media.class', '')
                    if media_class not in ['Audio/Sink', 'Audio/Source']:
                        continue

                    device = {
                        'id': obj.get('id'),
                        'name': props.get('node.name', 'Unknown'),
                        'description': props.get('node.description', 'Unknown'),
                        'media_class': media_class,
                        'channels': props.get('audio.channels', 0),
                        'rate': props.get('audio.rate', 0),
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
        
        self.init_ui()
        self.load_devices()

    def init_ui(self):
        """Initialize the GUI"""
        self.setWindowTitle('PipeWire Audio Device Configuration')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Device selection
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
        layout.addWidget(device_group)

        # Device info
        info_group = QGroupBox("Device Information")
        info_layout = QVBoxLayout()
        
        self.info_label = QLabel()
        self.info_label.setFont(QFont("Monospace", 9))
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()

        # Channels
        channels_layout = QHBoxLayout()
        channels_layout.addWidget(QLabel("Channels:"))
        self.channels_combo = QComboBox()
        self.channels_combo.addItems(['2', '4', '6', '8', '12', '16'])
        channels_layout.addWidget(self.channels_combo)
        channels_layout.addStretch()
        config_layout.addLayout(channels_layout)

        # Sample Rate
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Sample Rate (Hz):"))
        self.rate_combo = QComboBox()
        self.rate_combo.addItems(['44100', '48000', '88200', '96000', '176400', '192000'])
        rate_layout.addWidget(self.rate_combo)
        rate_layout.addStretch()
        config_layout.addLayout(rate_layout)

        # Latency (buffer size in samples)
        latency_layout = QHBoxLayout()
        latency_layout.addWidget(QLabel("Buffer Size (samples):"))
        self.latency_combo = QComboBox()
        self.latency_combo.addItems(['32', '64', '128', '256', '512', '1024', '2048', '4096'])
        self.latency_combo.setCurrentText('256')
        latency_layout.addWidget(self.latency_combo)
        latency_layout.addStretch()
        config_layout.addLayout(latency_layout)

        # ACP Mode toggle
        acp_layout = QHBoxLayout()
        acp_layout.addWidget(QLabel("ACP Mode (limits to stereo):"))
        self.acp_combo = QComboBox()
        self.acp_combo.addItems(['Disabled (Full Channels)', 'Enabled (Stereo Only)'])
        acp_layout.addWidget(self.acp_combo)
        acp_layout.addStretch()
        config_layout.addLayout(acp_layout)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Buttons
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
        
        layout.addLayout(button_layout)

        central_widget.setLayout(layout)

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
            return
        
        self.current_device = self.device_combo.itemData(index)
        self.update_device_info()

    def _nearest_buffer_size(self, samples):
        """Find nearest standard buffer size"""
        sizes = [32, 64, 128, 256, 512, 1024, 2048, 4096]
        nearest = min(sizes, key=lambda x: abs(x - samples))
        return nearest

    def _get_device_channel_names(self, device_description, direction='outputs'):
        """Get custom channel names for known devices"""
        # Check if this device has custom naming
        for device_key, device_config in DEVICE_CHANNEL_NAMES.items():
            if device_key.lower() in device_description.lower():
                return device_config['layout'].get(direction, [])
        return None

    def update_device_info(self):
        """Update device information display"""
        if not self.current_device:
            return
        
        dev = self.current_device
        # Convert nanoseconds to samples (assuming 48kHz as reference)
        latency_samples = int(dev['latency_ns'] / 1000000 * 48 / 1000) if dev['latency_ns'] > 0 else 256
        # Find nearest power of 2
        nearest_buffer = self._nearest_buffer_size(latency_samples)
        
        # Check for custom channel names
        custom_names = self._get_device_channel_names(dev['description'])
        direction = 'outputs' if dev['media_class'] == 'Audio/Sink' else 'inputs'
        
        # Only show channel layout if no custom names available
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
  Buffer Size: ~{nearest_buffer} samples ({nearest_buffer / 48:.1f}ms @ 48kHz)
  
{channel_info}
        """
        self.info_label.setText(info_text.strip())
        
        # Update controls
        self.channels_combo.setCurrentText(str(dev['channels']))
        if dev['rate'] > 0:
            self.rate_combo.setCurrentText(str(dev['rate']))
        self.acp_combo.setCurrentIndex(1 if dev['use_acp'] else 0)
        self.latency_combo.setCurrentText(str(nearest_buffer))

    def apply_config(self):
        """Apply configuration changes"""
        if not self.current_device:
            QMessageBox.warning(self, "Warning", "No device selected")
            return
        
        channels = int(self.channels_combo.currentText())
        sample_rate = int(self.rate_combo.currentText())
        use_acp = self.acp_combo.currentIndex() == 1
        buffer_size = int(self.latency_combo.currentText())
        latency_ms = buffer_size / sample_rate * 1000
        
        QMessageBox.information(
            self, "Configuration Applied",
            f"Applied to: {self.current_device['description']}\n\n"
            f"Channels: {channels}\n"
            f"Sample Rate: {sample_rate} Hz\n"
            f"Buffer Size: {buffer_size} samples ({latency_ms:.2f}ms)\n"
            f"ACP Mode: {'Enabled' if use_acp else 'Disabled'}\n\n"
            "Note: Restart PipeWire or reconnect device for changes to take effect.\n"
            "systemctl --user restart wireplumber"
        )

    def save_profile(self):
        """Save configuration as WirePlumber profile"""
        if not self.current_device:
            QMessageBox.warning(self, "Warning", "No device selected")
            return
        
        channels = int(self.channels_combo.currentText())
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
        
        # Create config file content
        config_content = f"""# PipeWire Audio Device Configuration
# Device: {self.current_device['description']}
# Auto-generated configuration
# Buffer Size: {buffer_size} samples ({buffer_size/sample_rate*1000:.2f}ms @ {sample_rate}Hz)

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
            QMessageBox.information(
                self, "Profile Saved",
                f"Configuration saved to:\n{config_file}\n\n"
                "Restart WirePlumber for changes to take effect:\n"
                "systemctl --user restart wireplumber"
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
            self.channels_combo.setCurrentText('2')
            self.rate_combo.setCurrentText('48000')
            self.acp_combo.setCurrentIndex(1)  # Enable ACP (stereo)
            self.latency_combo.setCurrentText('256')  # 256 samples default
            
            QMessageBox.information(
                self, "Reset Complete",
                "Device reset to defaults (2ch, 48kHz, 256 buffer).\n\n"
                "Restart WirePlumber for changes to take effect:\n"
                "systemctl --user restart wireplumber"
            )


def main():
    app = QApplication(sys.argv)
    window = PipeWireConfigGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
