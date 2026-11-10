"""Scrollable mixer panels with per-channel faders, mute, and solo controls for inputs and outputs."""

from typing import Dict, Optional, Any, List, Tuple
from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton,
    QWidget, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal

from ...core.alsa_mixer import get_fader_gain


class FaderStripPanel(QGroupBox):
    """Base panel containing scrollable hardware level faders with mute and solo controls."""

    gain_changed = pyqtSignal(str, int)  # (control_key, value)

    def __init__(
        self,
        default_title: str = "Mixer Levels",
        placeholder_text: str = "Hardware mixer controls are not available for the selected device.",
        is_output: bool = False,
        parent=None
    ):
        super().__init__(default_title, parent)
        self.default_title = default_title
        self.placeholder_text = placeholder_text
        self.is_output = is_output

        self.sliders: Dict[str, QSlider] = {}
        self.pct_labels: Dict[str, QLabel] = {}
        self.mute_buttons: Dict[str, QPushButton] = {}
        self.solo_buttons: Dict[str, QPushButton] = {}
        self.fader_control_keys: Dict[str, List[str]] = {}
        self.fader_mutes: Dict[str, int] = {}
        self.fader_solos: Dict[str, int] = {}

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Informative placeholder for devices without hardware mixer controls
        self.no_mixer_widget = QWidget()
        no_mixer_layout = QVBoxLayout()
        no_mixer_layout.setAlignment(Qt.AlignCenter)
        self.no_mixer_label = QLabel(self.placeholder_text)
        self.no_mixer_label.setAlignment(Qt.AlignCenter)
        self.no_mixer_label.setStyleSheet("color: #7f8c8d; font-size: 11px; font-weight: 500; padding: 6px;")
        no_mixer_layout.addWidget(self.no_mixer_label)
        self.no_mixer_widget.setLayout(no_mixer_layout)
        layout.addWidget(self.no_mixer_widget)

        # Scroll area for faders
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setMinimumHeight(190)
        self.scroll_area.setMaximumHeight(215)

        self.faders_container = QWidget()
        self.faders_layout = QHBoxLayout()
        self.faders_layout.setSpacing(6)
        self.faders_layout.setContentsMargins(4, 3, 4, 3)
        self.faders_container.setLayout(self.faders_layout)
        self.scroll_area.setWidget(self.faders_container)

        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

    def _get_controls_from_profile(self, profile: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Extract relevant mixer controls dictionary and capability flag from profile."""
        if self.is_output:
            has_mixer = bool(profile.get('has_output_mixer', False))
            controls = profile.get('output_mixer_controls', {})
        else:
            has_mixer = bool(profile.get('has_input_mixer', False))
            controls = profile.get('input_mixer_controls') or profile.get('mixer_controls', {})
        return has_mixer, controls

    def set_profile(self, profile: Optional[Dict[str, Any]], card_idx: Optional[int] = None):
        """Update mixer layout and visibility based on device profile."""
        if not profile:
            self.scroll_area.setVisible(False)
            self.no_mixer_widget.setVisible(True)
            self.setTitle(self.default_title)
            self.setToolTip("Hardware mixer controls not applicable for current device")
            self._clear_faders()
            return

        has_mixer, controls = self._get_controls_from_profile(profile)
        self.scroll_area.setVisible(has_mixer)
        self.no_mixer_widget.setVisible(not has_mixer)

        prefix = "Output Levels" if self.is_output else "Input Levels"
        if has_mixer:
            self.setTitle(f"{prefix} ({profile.get('name', 'Hardware Mixer')})")
            self.setToolTip(f"Hardware {prefix.lower()} for {profile.get('name', 'selected device')}")
            self._build_faders(controls, card_idx=card_idx)
        else:
            self.setTitle(self.default_title)
            self.setToolTip("Hardware mixer controls not applicable for current device")
            self._clear_faders()

    def _clear_faders(self):
        """Remove all existing fader widgets."""
        while self.faders_layout.count():
            item = self.faders_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.sliders.clear()
        self.pct_labels.clear()
        self.mute_buttons.clear()
        self.solo_buttons.clear()
        self.fader_control_keys.clear()
        self.fader_mutes.clear()
        self.fader_solos.clear()

    def _build_faders(self, mixer_controls: Dict[str, Any], card_idx: Optional[int] = None):
        """Construct fader columns from profile definition."""
        self._clear_faders()

        all_controls: List[Tuple[str, str, List[str]]] = []
        if isinstance(mixer_controls, dict):
            # Process known or arbitrary control groups (analog, spdif, adat, etc.)
            for group_key, controls in mixer_controls.items():
                if isinstance(controls, list):
                    for ctrl in controls:
                        if isinstance(ctrl, dict):
                            ctrl_key = ctrl.get('key')
                            keys = ctrl.get('keys')
                            if not keys and ctrl_key:
                                keys = [ctrl_key]
                            elif not ctrl_key and keys:
                                ctrl_key = keys[0]
                            label = ctrl.get('label', ctrl_key)
                            if ctrl_key and keys:
                                all_controls.append((ctrl_key, label, keys))
                        elif isinstance(ctrl, str):
                            all_controls.append((ctrl, ctrl, [ctrl]))

        for key, label_text, keys in all_controls:
            self.fader_control_keys[key] = keys

            col_widget = QWidget()
            col_layout = QVBoxLayout()
            col_layout.setAlignment(Qt.AlignCenter)
            col_layout.setContentsMargins(1, 1, 1, 1)
            col_layout.setSpacing(2)

            # Query current hardware value if card index available
            init_val = 0 if self.is_output else 65536
            if card_idx is not None and keys:
                hw_val = get_fader_gain(card_idx, keys[0])
                if hw_val is not None:
                    init_val = hw_val

            # Label
            lbl = QLabel(label_text)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 10px; font-weight: bold;")
            lbl.setMaximumWidth(88)
            col_layout.addWidget(lbl)

            # Fader
            slider = QSlider(Qt.Vertical)
            slider.setRange(0, 65536)
            slider.blockSignals(True)
            slider.setValue(init_val)
            slider.blockSignals(False)
            slider.setTickPosition(QSlider.TicksRight)
            slider.setTickInterval(16384)
            slider.setMinimumHeight(115)
            slider.setMaximumHeight(140)
            slider.valueChanged.connect(lambda val, k=key: self._on_fader_changed(k, val))
            self.sliders[key] = slider
            col_layout.addWidget(slider, alignment=Qt.AlignCenter)

            # Pct Label
            pct = int(round((init_val / 65536.0) * 100))
            pct_lbl = QLabel(f"{pct}%")
            pct_lbl.setAlignment(Qt.AlignCenter)
            pct_lbl.setStyleSheet("font-size: 10px;")
            self.pct_labels[key] = pct_lbl
            col_layout.addWidget(pct_lbl)

            # Button row (Mute + Solo)
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(3)
            btn_layout.setContentsMargins(0, 0, 0, 0)

            mute_btn = QPushButton("M")
            mute_btn.setCheckable(True)
            mute_btn.setFixedSize(26, 22)
            mute_btn.setStyleSheet("font-size: 10px; font-weight: bold;")
            mute_btn.setToolTip(f"Mute {label_text}")
            mute_btn.toggled.connect(lambda checked, k=key, s=slider: self._on_mute_toggled(k, checked, s))
            self.mute_buttons[key] = mute_btn
            btn_layout.addWidget(mute_btn)

            solo_btn = QPushButton("S")
            solo_btn.setCheckable(True)
            solo_btn.setFixedSize(26, 22)
            solo_btn.setStyleSheet("font-size: 10px; font-weight: bold;")
            solo_btn.setToolTip(f"Solo {label_text}")
            solo_btn.toggled.connect(lambda checked, k=key, s=slider: self._on_solo_toggled(k, checked, s))
            self.solo_buttons[key] = solo_btn
            btn_layout.addWidget(solo_btn)

            col_layout.addLayout(btn_layout)
            col_widget.setLayout(col_layout)
            self.faders_layout.addWidget(col_widget)

        self.faders_layout.addStretch()

    def _on_fader_changed(self, key: str, value: int):
        pct = int(round((value / 65536.0) * 100))
        if key in self.pct_labels:
            self.pct_labels[key].setText(f"{pct}%")

        if value > 0 and key in self.mute_buttons and self.mute_buttons[key].isChecked():
            self.mute_buttons[key].blockSignals(True)
            self.mute_buttons[key].setChecked(False)
            self.mute_buttons[key].setStyleSheet("font-size: 10px; font-weight: bold;")
            self.mute_buttons[key].blockSignals(False)

        any_solo = any(btn.isChecked() for btn in self.solo_buttons.values())
        if any_solo:
            self._sync_all_faders_hardware()
        else:
            is_muted = self.mute_buttons[key].isChecked() if key in self.mute_buttons else False
            effective_val = 0 if is_muted else value
            keys = self.fader_control_keys.get(key, [key])
            for k in keys:
                self.gain_changed.emit(k, effective_val)

    def _on_mute_toggled(self, key: str, checked: bool, slider: QSlider):
        mute_btn = self.mute_buttons.get(key)
        if mute_btn:
            if checked:
                mute_btn.setStyleSheet("font-size: 10px; font-weight: bold; background-color: #ffcccc; color: #cc0000;")
            else:
                mute_btn.setStyleSheet("font-size: 10px; font-weight: bold;")

        if checked:
            self.fader_mutes[key] = slider.value()
            slider.blockSignals(True)
            slider.setValue(0)
            slider.blockSignals(False)
            if key in self.pct_labels:
                self.pct_labels[key].setText("0%")
        else:
            stored_val = self.fader_mutes.get(key, 65536)
            slider.blockSignals(True)
            slider.setValue(stored_val)
            slider.blockSignals(False)
            pct = int(round((stored_val / 65536.0) * 100))
            if key in self.pct_labels:
                self.pct_labels[key].setText(f"{pct}%")

        self._sync_all_faders_hardware()

    def _on_solo_toggled(self, key: str, checked: bool, slider: QSlider):
        solo_btn = self.solo_buttons.get(key)
        if solo_btn:
            if checked:
                solo_btn.setStyleSheet("font-size: 10px; font-weight: bold; background-color: #ffe699; color: #b36b00;")
            else:
                solo_btn.setStyleSheet("font-size: 10px; font-weight: bold;")

        if checked:
            mute_btn = self.mute_buttons.get(key)
            if mute_btn and mute_btn.isChecked():
                mute_btn.blockSignals(True)
                mute_btn.setChecked(False)
                mute_btn.setStyleSheet("font-size: 10px; font-weight: bold;")
                mute_btn.blockSignals(False)
                stored_val = self.fader_mutes.get(key, 65536)
                slider.blockSignals(True)
                slider.setValue(stored_val)
                slider.blockSignals(False)
                pct = int(round((stored_val / 65536.0) * 100))
                if key in self.pct_labels:
                    self.pct_labels[key].setText(f"{pct}%")

        self._sync_all_faders_hardware()

    def _sync_all_faders_hardware(self):
        """Synchronize hardware levels accounting for active mute and solo routing."""
        any_solo = any(btn.isChecked() for btn in self.solo_buttons.values())

        for fader_id, s in self.sliders.items():
            if any_solo:
                is_soloed = self.solo_buttons[fader_id].isChecked() if fader_id in self.solo_buttons else False
                is_muted = self.mute_buttons[fader_id].isChecked() if fader_id in self.mute_buttons else False
                effective_val = s.value() if (is_soloed and not is_muted) else 0
            else:
                is_muted = self.mute_buttons[fader_id].isChecked() if fader_id in self.mute_buttons else False
                effective_val = 0 if is_muted else s.value()

            keys = self.fader_control_keys.get(fader_id, [fader_id])
            for k in keys:
                self.gain_changed.emit(k, effective_val)

    def poll_hardware_levels(self, card_idx: Optional[int]):
        """Poll live hardware levels and update sliders if changed externally (e.g. hardware knob)."""
        if card_idx is None or not self.sliders or not self.is_output:
            return
        for fader_id, slider in self.sliders.items():
            if slider.isSliderDown():
                continue  # User is currently dragging this slider in the UI
            keys = self.fader_control_keys.get(fader_id, [fader_id])
            if not keys:
                continue
            # Only poll master/encoder controls (such as Main-Out AN1/AN2)
            if len(keys) <= 1 and 'AN1' not in fader_id and 'AN2' not in fader_id:
                continue
            hw_val = get_fader_gain(card_idx, keys[0])
            if hw_val is not None and abs(hw_val - slider.value()) >= 100:
                slider.blockSignals(True)
                slider.setValue(hw_val)
                slider.blockSignals(False)
                pct = int(round((hw_val / 65536.0) * 100))
                if fader_id in self.pct_labels:
                    self.pct_labels[fader_id].setText(f"{pct}%")
                if hw_val > 0 and fader_id in self.mute_buttons and self.mute_buttons[fader_id].isChecked():
                    mute_btn = self.mute_buttons[fader_id]
                    mute_btn.blockSignals(True)
                    mute_btn.setChecked(False)
                    mute_btn.setStyleSheet("font-size: 10px; font-weight: bold;")
                    mute_btn.blockSignals(False)


class InputMixerPanel(FaderStripPanel):
    """Panel containing scrollable hardware input level faders."""

    def __init__(self, parent=None):
        super().__init__(
            default_title="Input Levels (ADAT & S/PDIF)",
            placeholder_text=(
                "Hardware input mixer controls are not available for the selected device.\n"
                "This panel is active for interfaces with dedicated ALSA mixer controls (e.g., RME Babyface Pro)."
            ),
            is_output=False,
            parent=parent
        )


class OutputMixerPanel(FaderStripPanel):
    """Panel containing scrollable hardware output level faders."""

    def __init__(self, parent=None):
        super().__init__(
            default_title="Output Levels (Main & ADAT)",
            placeholder_text=(
                "Hardware output mixer controls are not available for the selected device.\n"
                "This panel is active for interfaces with dedicated ALSA mixer controls (e.g., RME Babyface Pro)."
            ),
            is_output=True,
            parent=parent
        )
