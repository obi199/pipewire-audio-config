"""Device configuration panel widget."""

from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox
)
from PyQt5.QtCore import pyqtSignal

from ...core.config_builder import calculate_latency_ms


class DeviceConfigPanel(QGroupBox):
    """Configuration panel for ALSA path, channels, sample rate, buffer size, and ACP mode."""

    buffer_size_changed = pyqtSignal(int)
    sample_rate_changed = pyqtSignal(int)
    acp_mode_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__("Device Configuration", parent)
        self.init_ui()

    def init_ui(self):
        grid = QGridLayout()
        grid.setContentsMargins(8, 4, 8, 4)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(4)

        # Row 0, Col 0: ALSA Path
        alsa_path_layout = QHBoxLayout()
        alsa_path_layout.addWidget(QLabel("ALSA Path:"))
        self.alsa_path_label = QLabel("N/A")
        self.alsa_path_label.setStyleSheet("padding: 2px;")
        alsa_path_layout.addWidget(self.alsa_path_label)
        alsa_path_layout.addStretch()
        grid.addLayout(alsa_path_layout, 0, 0)

        # Row 1, Col 0: Channels
        channels_layout = QHBoxLayout()
        channels_layout.addWidget(QLabel("Channels:"))
        self.channels_label = QLabel()
        self.channels_label.setStyleSheet("padding: 2px;")
        channels_layout.addWidget(self.channels_label)
        channels_layout.addStretch()
        grid.addLayout(channels_layout, 1, 0)

        # Row 0, Col 1: Sample Rate
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Sample Rate (Hz):"))
        self.rate_combo = QComboBox()
        self.rate_combo.addItems(['44100', '48000', '88200', '96000', '176400', '192000'])
        self.rate_combo.currentIndexChanged.connect(self._on_rate_changed)
        rate_layout.addWidget(self.rate_combo)
        grid.addLayout(rate_layout, 0, 1)

        # Row 1, Col 1: Calculated Latency
        calc_latency_layout = QHBoxLayout()
        calc_latency_layout.addWidget(QLabel("Latency:"))
        self.calc_latency_label = QLabel("N/A")
        self.calc_latency_label.setStyleSheet("padding: 2px; font-weight: bold;")
        calc_latency_layout.addWidget(self.calc_latency_label)
        calc_latency_layout.addStretch()
        grid.addLayout(calc_latency_layout, 1, 1)

        # Row 0, Col 2: Buffer Size (samples)
        latency_layout = QHBoxLayout()
        latency_layout.addWidget(QLabel("Buffer Size (samples):"))
        self.latency_combo = QComboBox()
        self.latency_combo.addItems(['32', '64', '128', '256', '512', '1024', '2048', '4096'])
        self.latency_combo.setCurrentText('256')
        self.latency_combo.currentIndexChanged.connect(self._on_buffer_changed)
        latency_layout.addWidget(self.latency_combo)
        grid.addLayout(latency_layout, 0, 2)

        # Row 1, Col 2: ACP Mode
        acp_layout = QHBoxLayout()
        acp_layout.addWidget(QLabel("ACP Mode (limits to stereo):"))
        self.acp_combo = QComboBox()
        self.acp_combo.addItems(['Disabled (multi-channel enabled)', 'Enabled (stereo only)'])
        self.acp_combo.currentIndexChanged.connect(self._on_acp_changed)
        acp_layout.addWidget(self.acp_combo)
        grid.addLayout(acp_layout, 1, 2)

        self.setLayout(grid)

    def _on_rate_changed(self, index: int):
        self.update_calculated_latency()
        try:
            rate = int(self.rate_combo.currentText())
            self.sample_rate_changed.emit(rate)
        except ValueError:
            pass

    def _on_buffer_changed(self, index: int):
        self.update_calculated_latency()
        try:
            buf = int(self.latency_combo.currentText())
            self.buffer_size_changed.emit(buf)
        except ValueError:
            pass

    def _on_acp_changed(self, index: int):
        use_acp = (index == 1)
        self.acp_mode_changed.emit(use_acp)

    def update_calculated_latency(self):
        """Update calculated latency display dynamically."""
        try:
            buffer_size = int(self.latency_combo.currentText())
            sample_rate = int(self.rate_combo.currentText())
            if sample_rate > 0:
                latency_ms = calculate_latency_ms(buffer_size, sample_rate)
                self.calc_latency_label.setText(f"{latency_ms:.2f} ms ({buffer_size} samples @ {sample_rate} Hz)")
            else:
                self.calc_latency_label.setText("N/A")
        except (ValueError, TypeError, AttributeError):
            self.calc_latency_label.setText("N/A")

    def update_device(self, device: Optional[Dict[str, Any]], nearest_buffer: int = 256):
        """Populate widget state from device dictionary."""
        if not device:
            self.alsa_path_label.setText("N/A")
            self.channels_label.setText("")
            self.calc_latency_label.setText("N/A")
            return

        self.alsa_path_label.setText(device.get('alsa_path', '') or 'N/A')
        self.channels_label.setText(str(device.get('channels', 0)))

        self.rate_combo.blockSignals(True)
        dev_rate = device.get('rate', 0)
        if dev_rate > 0:
            self.rate_combo.setCurrentText(str(dev_rate))
        self.rate_combo.blockSignals(False)

        self.acp_combo.blockSignals(True)
        self.acp_combo.setCurrentIndex(1 if device.get('use_acp') else 0)
        self.acp_combo.blockSignals(False)

        # Disable ACP toggle for Babyface Pro
        if "Babyface" in device.get("description", ""):
            self.acp_combo.setEnabled(False)
            self.acp_combo.setToolTip("ACP mode not recommended for Babyface Pro (disables ADAT/SPDIF)")
        else:
            self.acp_combo.setEnabled(True)
            self.acp_combo.setToolTip("")

        self.latency_combo.blockSignals(True)
        self.latency_combo.setCurrentText(str(nearest_buffer))
        self.latency_combo.blockSignals(False)

        self.update_calculated_latency()

    def get_settings(self) -> Dict[str, Any]:
        """Return the current configuration settings."""
        try:
            rate = int(self.rate_combo.currentText())
        except ValueError:
            rate = 48000

        try:
            buffer_size = int(self.latency_combo.currentText())
        except ValueError:
            buffer_size = 256

        return {
            'channels': int(self.channels_label.text()) if self.channels_label.text().isdigit() else 2,
            'rate': rate,
            'buffer_size': buffer_size,
            'use_acp': self.acp_combo.currentIndex() == 1,
        }
