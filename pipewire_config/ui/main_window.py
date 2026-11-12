"""Main application window coordinating UI widgets and backend services."""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Any

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QGroupBox, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

from ..core.detector import detect_devices
from ..core.config_builder import (
    generate_wireplumber_config,
    write_wireplumber_config,
    nearest_buffer_size,
    get_config_path
)
from ..core.alsa_mixer import (
    get_alsa_card_index,
    apply_fader_gain,
    apply_startup_control_map,
    apply_input_gain,
    get_wpctl_device_id,
    apply_volume,
    apply_mute,
    get_wpctl_volume_and_mute
)
from ..core.service import restart_wireplumber
from ..profiles.loader import get_profile_loader, ProfileLoader

from .widgets.config_panel import DeviceConfigPanel
from .widgets.fader_strip import InputMixerPanel, OutputMixerPanel


class DeviceDetectorThread(QThread):
    """Background worker thread to detect PipeWire audio devices."""
    devices_found = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            devices = detect_devices(timeout=5)
            self.devices_found.emit(devices)
        except Exception as e:
            self.error.emit(str(e))


class ServiceRestartWorkerThread(QThread):
    """Background worker thread to restart WirePlumber service asynchronously."""
    finished = pyqtSignal(bool, str)

    def run(self):
        success, message = restart_wireplumber(timeout=10, wait_delay=2.0)
        self.finished.emit(success, message)


class MainWindow(QMainWindow):
    """Primary application window coordinating device discovery, configuration, and mixer controls."""

    def __init__(self, profile_loader: Optional[ProfileLoader] = None):
        super().__init__()
        self.profile_loader = profile_loader or get_profile_loader()
        self.devices: List[Dict[str, Any]] = []
        self.current_device: Optional[Dict[str, Any]] = None
        self.is_restarting = False
        self.ignore_buffer_changes = False

        self._pending_gains: Dict[str, int] = {}
        self._last_fader_interaction_time: float = 0.0

        self._gain_timer = QTimer(self)
        self._gain_timer.setSingleShot(True)
        self._gain_timer.timeout.connect(self._flush_fader_gains)

        self.init_ui()
        self.load_devices()

    def init_ui(self):
        self.setWindowTitle('PipeWire Audio Device Configuration')
        self.setGeometry(100, 100, 1050, 650)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        # Top bar: Device selector and Refresh
        device_group = QGroupBox("Audio Devices")
        device_layout = QHBoxLayout()
        device_layout.setContentsMargins(6, 4, 6, 4)
        device_layout.setSpacing(6)

        device_layout.addWidget(QLabel("Select Device:"))
        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        device_layout.addWidget(self.device_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_devices)
        device_layout.addWidget(refresh_btn)

        device_group.setLayout(device_layout)
        main_layout.addWidget(device_group)

        # Device Configuration Panel
        self.config_panel = DeviceConfigPanel()
        self.config_panel.buffer_size_changed.connect(self.on_buffer_size_changed)
        self.config_panel.sample_rate_changed.connect(self.on_sample_rate_changed)
        self.config_panel.acp_mode_changed.connect(self.on_acp_mode_changed)
        main_layout.addWidget(self.config_panel)

        # Input Levels Mixer Panel
        self.input_mixer_panel = InputMixerPanel()
        self.input_mixer_panel.gain_changed.connect(self.on_fader_gain_changed)
        self.mixer_panel = self.input_mixer_panel  # backward-compatible reference
        main_layout.addWidget(self.input_mixer_panel)

        # Output Levels Mixer Panel
        self.output_mixer_panel = OutputMixerPanel()
        self.output_mixer_panel.gain_changed.connect(self.on_fader_gain_changed)
        main_layout.addWidget(self.output_mixer_panel)

        # Action Buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_profile)
        btn_layout.addWidget(save_btn)

        apply_btn = QPushButton("Apply & Restart WirePlumber")
        apply_btn.clicked.connect(self.apply_config)
        btn_layout.addWidget(apply_btn)

        restart_btn = QPushButton("Restart WirePlumber")
        restart_btn.clicked.connect(self.restart_wireplumber)
        btn_layout.addWidget(restart_btn)

        main_layout.addLayout(btn_layout)
        central_widget.setLayout(main_layout)

        self.statusBar().showMessage("Ready")

    def load_devices(self):
        """Asynchronously load PipeWire devices using background worker."""
        self.statusBar().showMessage("Detecting PipeWire devices...")
        self.device_combo.setEnabled(False)

        self.detector = DeviceDetectorThread()
        self.detector.devices_found.connect(self._on_devices_found)
        self.detector.error.connect(self._on_detector_error)
        self.detector.start()

    def _on_devices_found(self, devices: List[Dict[str, Any]]):
        self.devices = devices
        self.device_combo.setEnabled(True)
        self.device_combo.blockSignals(True)
        self.device_combo.clear()

        if not self.devices:
            self.statusBar().showMessage("No ALSA devices found")
            self.config_panel.update_device(None)
            self.input_mixer_panel.set_profile(None)
            self.output_mixer_panel.set_profile(None)
            self.device_combo.blockSignals(False)
            return

        for dev in self.devices:
            label = f"{dev['description']} ({'Output' if dev['media_class'] == 'Audio/Sink' else 'Input'})"
            self.device_combo.addItem(label)

        self.device_combo.blockSignals(False)
        self.device_combo.setCurrentIndex(0)
        self.on_device_changed(0)
        self.statusBar().showMessage(f"Found {len(self.devices)} devices")

    def _on_detector_error(self, message: str):
        self.device_combo.setEnabled(True)
        self.statusBar().showMessage(f"Error: {message}")
        QMessageBox.warning(self, "Detection Error", f"Failed to detect devices:\n\n{message}")

    def on_device_changed(self, index: int):
        """Handle device selection change."""
        if index < 0 or not self.devices or index >= len(self.devices):
            self.current_device = None
            self.config_panel.update_device(None)
            self.input_mixer_panel.set_profile(None)
            self.output_mixer_panel.set_profile(None)
            return

        self.current_device = self.devices[index]

        dev = self.current_device
        latency_ns = dev.get('latency_ns', 0)
        rate = dev.get('rate', 48000) or 48000
        latency_samples = int(round((latency_ns / 1e9) * rate)) if rate > 0 else 256
        nearest_buf = nearest_buffer_size(latency_samples)

        self.config_panel.update_device(dev, nearest_buf)

        card_idx = get_alsa_card_index(dev)
        profile = self.profile_loader.get_profile_for_device(dev.get('description', ''))
        self.input_mixer_panel.set_profile(profile, card_idx=card_idx)
        self.output_mixer_panel.set_profile(profile, card_idx=card_idx)

        if profile and dev.get('media_class') == 'Audio/Sink':
            startup_controls = profile.get('startup_routing_controls', [])
            if isinstance(startup_controls, list):
                apply_startup_control_map(card_idx, startup_controls)

    def on_fader_gain_changed(self, control_key: str, value: int):
        self._last_fader_interaction_time = time.time()
        self._pending_gains[control_key] = value
        self._gain_timer.start(40)

    on_input_gain_changed = on_fader_gain_changed

    def _flush_fader_gains(self):
        if not self.current_device or not self._pending_gains:
            return
        card_idx = get_alsa_card_index(self.current_device)
        for ctrl_key, val in list(self._pending_gains.items()):
            apply_fader_gain(card_idx, ctrl_key, val)
        self._pending_gains.clear()

    _flush_input_gains = _flush_fader_gains

    def _generate_current_config(self) -> Optional[str]:
        if not self.current_device:
            return None

        dev = self.current_device
        settings = self.config_panel.get_settings()
        rate = settings['rate']
        buffer_size = settings['buffer_size']
        latency_ns = int((buffer_size / rate) * 1e9) if rate > 0 else 0
        use_acp = settings['use_acp']
        channels = settings['channels']

        direction = 'outputs' if dev['media_class'] == 'Audio/Sink' else 'inputs'
        custom_names = self.profile_loader.get_channel_names(dev['description'], direction)

        return generate_wireplumber_config(
            device_name=dev['name'],
            channels=channels,
            rate=rate,
            latency_ns=latency_ns,
            use_acp=use_acp,
            channel_names=custom_names,
            description=dev['description']
        )

    def on_buffer_size_changed(self, buffer_size: int):
        if not self.current_device or self.ignore_buffer_changes:
            return
        config_text = self._generate_current_config()
        if config_text:
            try:
                write_wireplumber_config(self.current_device['name'], config_text)
                self.statusBar().showMessage(f"Buffer size saved: {buffer_size} samples")
            except Exception as e:
                self.statusBar().showMessage(f"Failed to write config: {str(e)}")

    def on_sample_rate_changed(self, rate: int):
        if not self.current_device or self.ignore_buffer_changes:
            return
        config_text = self._generate_current_config()
        if config_text:
            try:
                write_wireplumber_config(self.current_device['name'], config_text)
                self.statusBar().showMessage(f"Sample rate saved: {rate} Hz")
            except Exception as e:
                self.statusBar().showMessage(f"Failed to write config: {str(e)}")

    def on_acp_mode_changed(self, use_acp: bool):
        if not self.current_device or self.ignore_buffer_changes:
            return
        config_text = self._generate_current_config()
        if config_text:
            try:
                write_wireplumber_config(self.current_device['name'], config_text)
                self.statusBar().showMessage(f"ACP Mode saved: {'Enabled' if use_acp else 'Disabled'}")
            except Exception as e:
                self.statusBar().showMessage(f"Failed to write config: {str(e)}")

    def save_profile(self):
        """Save configuration without restarting service."""
        if not self.current_device:
            QMessageBox.warning(self, "Warning", "No device selected")
            return

        config_text = self._generate_current_config()
        if not config_text:
            return

        try:
            config_file = write_wireplumber_config(self.current_device['name'], config_text)
            self.statusBar().showMessage(f"Configuration saved to {config_file.name}")
            QMessageBox.information(
                self, "Success",
                f"Configuration saved to:\n{config_file}\n\n"
                f"Settings:\n"
                f"• Rate: {self.config_panel.get_settings()['rate']} Hz\n"
                f"• Buffer: {self.config_panel.get_settings()['buffer_size']} samples\n"
                f"• ACP Mode: {'Enabled' if self.config_panel.get_settings()['use_acp'] else 'Disabled'}\n\n"
                f"Click 'Restart WirePlumber' to apply changes."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration:\n\n{str(e)}")

    def apply_config(self):
        """Save configuration and restart WirePlumber."""
        if not self.current_device:
            QMessageBox.warning(self, "Warning", "No device selected")
            return

        config_text = self._generate_current_config()
        if not config_text:
            return

        try:
            write_wireplumber_config(self.current_device['name'], config_text)
            self.restart_wireplumber()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to write config:\n\n{str(e)}")

    def restart_wireplumber(self):
        """Asynchronously restart WirePlumber service."""
        if self.is_restarting:
            return

        self.is_restarting = True
        self.ignore_buffer_changes = True
        self.statusBar().showMessage("Restarting WirePlumber...")

        self.restart_worker = ServiceRestartWorkerThread()
        self.restart_worker.finished.connect(self._on_restart_finished)
        self.restart_worker.start()

    def _on_restart_finished(self, success: bool, message: str):
        self.is_restarting = False
        self.ignore_buffer_changes = False

        if success:
            self.statusBar().showMessage("WirePlumber restarted successfully")
            QMessageBox.information(self, "Success", message)
            self.load_devices()
        else:
            self.statusBar().showMessage("Failed to restart WirePlumber")
            QMessageBox.critical(self, "Error", message)

    def activate_window_to_front(self):
        """Bring the application window to foreground and give it focus."""
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """Clean up resources on window close."""
        if hasattr(self, '_poll_timer') and self._poll_timer:
            self._poll_timer.stop()
        if hasattr(self, 'detector') and self.detector and self.detector.isRunning():
            self.detector.wait(2000)
        if hasattr(self, 'restart_worker') and self.restart_worker and self.restart_worker.isRunning():
            self.restart_worker.wait(2000)
        if hasattr(self, '_instance_mgr') and self._instance_mgr:
            self._instance_mgr.close()
        super().closeEvent(event)


class SingleInstanceManager:
    """Manages single-instance enforcement via QLocalServer / QLocalSocket."""

    def __init__(self, server_name: Optional[str] = None):
        if server_name is None:
            uid = os.getuid() if hasattr(os, 'getuid') else 'user'
            server_name = f"pipewire_audio_config_{uid}"
        self.server_name = server_name
        self.server: Optional[QLocalServer] = None

    def is_another_instance_running(self, timeout_ms: int = 500) -> bool:
        """Check if another primary instance is listening and signal it to activate."""
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        if socket.waitForConnected(timeout_ms):
            socket.write(b"ACTIVATE\n")
            socket.waitForBytesWritten(timeout_ms)
            socket.disconnectFromServer()
            return True
        return False

    def start_server(self, on_activate_callback) -> bool:
        """Start listening for secondary instances."""
        QLocalServer.removeServer(self.server_name)
        self.server = QLocalServer()

        def handle_new_connection():
            if not self.server:
                return
            client = self.server.nextPendingConnection()
            if client:
                client.disconnected.connect(client.deleteLater)
            if callable(on_activate_callback):
                on_activate_callback()

        self.server.newConnection.connect(handle_new_connection)
        return self.server.listen(self.server_name)

    def close(self):
        """Close local server and cleanup socket."""
        if self.server:
            self.server.close()
            QLocalServer.removeServer(self.server_name)
            self.server = None


def main(argv: Optional[List[str]] = None) -> int:
    """Application entry point with single-instance enforcement."""
    args = argv if argv is not None else sys.argv
    app = QApplication.instance() or QApplication(args)

    instance_mgr = SingleInstanceManager()
    if instance_mgr.is_another_instance_running():
        print("Another instance of PipeWire Audio Config is already running. Activating existing window.")
        return 0

    window = MainWindow()
    instance_mgr.start_server(window.activate_window_to_front)
    window._instance_mgr = instance_mgr

    window.show()
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
