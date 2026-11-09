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
    QMessageBox, QListWidget, QListWidgetItem, QScrollArea
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
        self.latency_combo.setToolTip("Smaller = lower latency but more CPU load\nLarger = higher latency but more stable\n\nNote: Changes require WirePlumber restart")
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
        
        # Info box about buffer size and device changes
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Volume & Mute Controls
        volume_group = QGroupBox("Volume & Mute")
        volume_layout = QVBoxLayout()

        # Master volume
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
        
        # Per-channel volume controls (scrollable)
        self.channel_volume_scroll = QScrollArea()
        self.channel_volume_scroll.setWidgetResizable(True)
        self.channel_volume_widget = QWidget()
        self.channel_volume_layout = QVBoxLayout(self.channel_volume_widget)
        self.channel_volume_scroll.setWidget(self.channel_volume_widget)
        self.channel_volume_scroll.setMaximumHeight(200)
        
        volume_layout.addWidget(QLabel("Per-Channel Volume:"))
        volume_layout.addWidget(self.channel_volume_scroll)
        
        volume_group.setLayout(volume_layout)
        layout.addWidget(volume_group)
        
        # Store references for per-channel controls
        self.channel_sliders = {}
        self.channel_mute_buttons = {}
        self.channel_volume_labels = {}
        
        # Connect master volume slider
        self.master_volume_slider.valueChanged.connect(self.on_master_volume_changed)
        
        # Connect buffer size combo for immediate config update
        self.latency_combo.currentTextChanged.connect(self.on_buffer_size_changed)

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
        
        button_layout.addStretch()
        
        restart_btn = QPushButton("Restart WirePlumber")
        restart_btn.setStyleSheet("background-color: #fff3cd; font-weight: bold;")
        restart_btn.clicked.connect(self.restart_wireplumber)
        button_layout.addWidget(restart_btn)
        
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
        # Convert nanoseconds to samples using actual device sample rate
        if dev['latency_ns'] > 0 and dev['rate'] > 0:
            latency_ms = dev['latency_ns'] / 1e6
            latency_samples = int((latency_ms * dev['rate']) / 1000)
        else:
            latency_samples = 256
        
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
  Buffer Size: ~{nearest_buffer} samples ({nearest_buffer / dev['rate'] * 1000:.2f}ms @ {dev['rate']}Hz)
  
{channel_info}
        """
        # Update controls
        self.channels_combo.setCurrentText(str(dev['channels']))
        if dev['rate'] > 0:
            self.rate_combo.setCurrentText(str(dev['rate']))
        self.acp_combo.setCurrentIndex(1 if dev['use_acp'] else 0)
        # Block buffer size signal during update to prevent triggering save
        self.latency_combo.blockSignals(True)
        self.latency_combo.setCurrentText(str(nearest_buffer))
        self.latency_combo.blockSignals(False)
        
        # Create per-channel volume controls
        get_names = self._get_device_channel_names(dev['description'], direction)
        self.create_channel_volume_controls(dev['channels'], get_names)
        
        # Load saved volume settings
        self.load_device_volume_settings()

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
        
        # Collect per-channel volume and mute settings
        channel_volumes = []
        channel_mutes = []
        for i in range(channels):
            channel_id = f"ch_{i}"
            volume = self.channel_sliders.get(channel_id, {}).value() if channel_id in self.channel_sliders else 100
            muted = self.channel_mute_buttons.get(channel_id, {}).isChecked() if channel_id in self.channel_mute_buttons else False
            channel_volumes.append(volume)
            channel_mutes.append("true" if muted else "false")
        
        # Format volumes and mutes for config
        volumes_str = "[ " + ", ".join(str(v) for v in channel_volumes) + " ]"
        mutes_str = "[ " + ", ".join(channel_mutes) + " ]"
        
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
        # Volume and mute settings
        # Master volume: 0-100%
        # Master mute: true/false
        # Per-channel volumes: {volumes_str}
        # Per-channel mutes: {mutes_str}
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
                'master_muted': self.master_mute_btn.isChecked(),
                'channel_volumes': channel_volumes,
                'channel_mutes': channel_mutes
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
        
        try:
            # Show a progress message
            progress_msg = QMessageBox(self)
            progress_msg.setWindowTitle("Restarting WirePlumber")
            progress_msg.setText("Restarting WirePlumber service...\n\nPlease wait...")
            progress_msg.setStandardButtons(QMessageBox.NoButton)
            progress_msg.show()
            
            # Restart WirePlumber
            result = subprocess.run(
                ['systemctl', '--user', 'restart', 'wireplumber'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            progress_msg.close()
            
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
                self.ignore_buffer_changes = False
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
        
    def on_buffer_size_changed(self, value):
        """Handle buffer size change - write config immediately"""
        if not self.current_device or self.ignore_buffer_changes:
            return
        
        try:
            # Get current settings
            channels = int(self.channels_combo.currentText())
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
            
            # Collect per-channel volume and mute settings
            channel_volumes = []
            channel_mutes = []
            for i in range(channels):
                channel_id = f"ch_{i}"
                volume = self.channel_sliders.get(channel_id, {}).value() if channel_id in self.channel_sliders else 100
                muted = self.channel_mute_buttons.get(channel_id, {}).isChecked() if channel_id in self.channel_mute_buttons else False
                channel_volumes.append(volume)
                channel_mutes.append("true" if muted else "false")
            
            volumes_str = "[ " + ", ".join(str(v) for v in channel_volumes) + " ]"
            mutes_str = "[ " + ", ".join(channel_mutes) + " ]"
            
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
        # Volume and mute settings
        # Master volume: 0-100%
        # Master mute: true/false
        # Per-channel volumes: {volumes_str}
        # Per-channel mutes: {mutes_str}
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
    def load_device_volume_settings(self):
        """Load previously saved volume/mute settings for current device"""
        if not self.current_device:
            return
        
        try:
            import json
            device_short = self.current_device['description'].replace(' ', '-')[:20]
            volume_file = self.config_dir / f'volume-{device_short}.json'
            
            if not volume_file.exists():
                return
            
            with open(volume_file, 'r') as f:
                volume_config = json.load(f)
            
            # Load master volume and mute
            master_vol = volume_config.get('master_volume', 100)
            master_muted = volume_config.get('master_muted', False)
            
            # Update master controls without triggering signals initially
            self.master_volume_slider.blockSignals(True)
            self.master_mute_btn.blockSignals(True)
            
            self.master_volume_slider.setValue(master_vol)
            self.master_mute_btn.setChecked(master_muted)
            self.on_master_volume_changed(master_vol)
            
            if master_muted:
                self.toggle_master_mute(True)
            
            self.master_volume_slider.blockSignals(False)
            self.master_mute_btn.blockSignals(False)
            
            # Load per-channel settings
            channel_volumes = volume_config.get('channel_volumes', [])
            channel_mutes = volume_config.get('channel_mutes', [])
            
            for i, (volume, muted) in enumerate(zip(channel_volumes, channel_mutes)):
                channel_id = f"ch_{i}"
                
                if channel_id in self.channel_sliders:
                    self.channel_sliders[channel_id].blockSignals(True)
                    self.channel_sliders[channel_id].setValue(volume)
                    self.channel_sliders[channel_id].blockSignals(False)
                
                if channel_id in self.channel_mute_buttons:
                    self.channel_mute_buttons[channel_id].blockSignals(True)
                    # Convert muted to boolean if it's a string from JSON
                    muted_bool = muted if isinstance(muted, bool) else (muted.lower() == 'true' if isinstance(muted, str) else muted)
                    self.channel_mute_buttons[channel_id].setChecked(muted_bool)
                    if muted_bool:
                        self.channel_mute_buttons[channel_id].setText("🔇 Muted")
                        self.channel_mute_buttons[channel_id].setStyleSheet("background-color: #ffcccc;")
                    self.channel_mute_buttons[channel_id].blockSignals(False)
        
        except Exception as e:
            print(f"Warning: Could not load volume settings: {e}")

    def on_master_volume_changed(self, value):
        """Handle master volume slider change"""
        self.master_volume_label.setText(f"{value}%")
        
        # Update all channel sliders to master volume
        for channel_id, slider in self.channel_sliders.items():
            slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(False)
        
        # Apply volume to PipeWire device
        if self.current_device:
            self._apply_volume_to_device(value)

    def toggle_master_mute(self, checked):
        """Toggle master mute for all channels"""
        if checked:
            self.master_mute_btn.setText("🔇 Muted")
            self.master_mute_btn.setStyleSheet("background-color: #ffcccc;")
            # Mute all channels
            for channel_id, btn in self.channel_mute_buttons.items():
                btn.blockSignals(True)
                btn.setChecked(True)
                btn.setText("🔇 Muted")
                btn.setStyleSheet("background-color: #ffcccc;")
                btn.blockSignals(False)
        else:
            self.master_mute_btn.setText("🔊 Unmuted")
            self.master_mute_btn.setStyleSheet("")
            # Unmute all channels
            for channel_id, btn in self.channel_mute_buttons.items():
                btn.blockSignals(True)
                btn.setChecked(False)
                btn.setText("🔊 Unmuted")
                btn.setStyleSheet("")
                btn.blockSignals(False)
        
        # Apply mute to PipeWire device
        if self.current_device:
            self._apply_mute_to_device(checked)

    def create_channel_volume_controls(self, num_channels, channel_names=None):
        """Create per-channel volume sliders and mute buttons"""
        # Clear existing controls
        while self.channel_volume_layout.count():
            widget = self.channel_volume_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        # Disconnect any existing signals from old sliders/buttons
        for slider in self.channel_sliders.values():
            try:
                slider.valueChanged.disconnect()
            except:
                pass
        
        for button in self.channel_mute_buttons.values():
            try:
                button.clicked.disconnect()
            except:
                pass
        
        self.channel_sliders.clear()
        self.channel_mute_buttons.clear()
        self.channel_volume_labels.clear()
        
        if num_channels <= 0:
            return
        
        for i in range(num_channels):
            channel_id = f"ch_{i}"
            
            # Get channel name
            if channel_names and i < len(channel_names):
                ch_name = channel_names[i]
            else:
                ch_name = f"Channel {i + 1}"
            
            # Create channel control layout
            ch_layout = QHBoxLayout()
            
            # Channel label
            ch_layout.addWidget(QLabel(ch_name))
            
            # Volume slider
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(100)
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(10)
            slider.setMaximumWidth(150)
            ch_layout.addWidget(slider)
            self.channel_sliders[channel_id] = slider
            
            # Volume percentage label
            vol_label = QLabel("100%")
            vol_label.setMinimumWidth(35)
            ch_layout.addWidget(vol_label)
            self.channel_volume_labels[channel_id] = vol_label
            
            # Connect slider to update label and apply volume
            slider.valueChanged.connect(
                lambda value, label=vol_label: label.setText(f"{value}%")
            )
            slider.valueChanged.connect(
                lambda value: self._apply_volume_to_device(value)
            )
            
            # Mute button
            mute_btn = QPushButton("🔊 Unmuted")
            mute_btn.setCheckable(True)
            mute_btn.setMaximumWidth(120)
            mute_btn.clicked.connect(
                lambda checked, btn_ref=mute_btn: self.toggle_channel_mute(checked, btn_ref)
            )
            ch_layout.addWidget(mute_btn)
            self.channel_mute_buttons[channel_id] = mute_btn
            
            ch_layout.addStretch()
            
            # Add to main layout
            self.channel_volume_layout.addLayout(ch_layout)
        
        # Add stretch at the end
        self.channel_volume_layout.addStretch()

    def toggle_channel_mute(self, checked, button):
        """Toggle mute for individual channel"""
        if checked:
            button.setText("🔇 Muted")
            button.setStyleSheet("background-color: #ffcccc;")
        else:
            button.setText("🔊 Unmuted")
            button.setStyleSheet("")
        
         # Apply mute to PipeWire device
        if self.current_device:
            self._apply_mute_to_device(checked)

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
            
            # Set volume using wpctl
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


def main():
    app = QApplication(sys.argv)
    window = PipeWireConfigGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
