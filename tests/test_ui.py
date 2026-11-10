"""Headless tests for PyQt5 widgets and UI interactions."""

import os
import unittest
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt5.QtWidgets import QApplication
from pipewire_config.ui.widgets.config_panel import DeviceConfigPanel
from pipewire_config.ui.widgets.fader_strip import InputMixerPanel, OutputMixerPanel
from pipewire_config.ui.main_window import MainWindow, SingleInstanceManager
from pipewire_config.profiles.loader import ProfileLoader

# Shared QApplication instance for test execution
app = QApplication.instance() or QApplication([])


class TestUIWidgets(unittest.TestCase):

    def test_config_panel_latency_calculation(self):
        panel = DeviceConfigPanel()
        panel.latency_combo.setCurrentText("128")
        panel.rate_combo.setCurrentText("48000")
        panel.update_calculated_latency()
        self.assertIn("2.67 ms", panel.calc_latency_label.text())

        panel.latency_combo.setCurrentText("512")
        panel.rate_combo.setCurrentText("96000")
        panel.update_calculated_latency()
        self.assertIn("5.33 ms", panel.calc_latency_label.text())

    def test_input_fader_strip_solo_and_mute(self):
        loader = ProfileLoader()
        profile = loader.get_profile_for_device("Babyface Pro")

        panel = InputMixerPanel()
        panel.set_profile(profile)

        self.assertEqual(len(panel.sliders), 28)
        self.assertIn("Mic-AN1 Gain", panel.sliders)
        self.assertIn("Mic-AN1-AN1", panel.sliders)
        self.assertIn("Line-AS1-AN1", panel.sliders)

        emitted_gains = {}
        panel.gain_changed.connect(lambda k, v: emitted_gains.update({k: v}))

        # Mute first fader
        mute_btn = panel.mute_buttons["Line-AS1-AN1"]
        mute_btn.setChecked(True)
        self.assertEqual(emitted_gains["Line-AS1-AN1"], 0)
        self.assertEqual(panel.pct_labels["Line-AS1-AN1"].text(), "0%")

        # Unmute restores level
        mute_btn.setChecked(False)
        self.assertEqual(emitted_gains["Line-AS1-AN1"], 65536)
        self.assertEqual(panel.pct_labels["Line-AS1-AN1"].text(), "100%")

        # Solo a channel
        solo_btn = panel.solo_buttons["Line-AS1-AN1"]
        solo_btn.setChecked(True)
        # Solo channel should be active (65536), other channels suppressed to 0
        self.assertEqual(emitted_gains["Line-AS1-AN1"], 65536)
        self.assertEqual(emitted_gains["Line-AS1-AN2"], 0)

        # Turn off solo
        solo_btn.setChecked(False)
        self.assertEqual(emitted_gains["Line-AS1-AN2"], 65536)

    def test_output_fader_strip_solo_and_mute(self):
        loader = ProfileLoader()
        profile = loader.get_profile_for_device("Babyface Pro")

        panel = OutputMixerPanel()
        panel.set_profile(profile)

        # 1 stereo pair (Main AN1/AN2) + 10 mono outputs (Phones, SPDIF, ADAT 1-6) = 11 output faders
        self.assertEqual(len(panel.sliders), 11)
        self.assertIn("Main-Out AN1/AN2", panel.sliders)
        self.assertIn("Main-Out PH3", panel.sliders)
        self.assertIn("Main-Out AS1", panel.sliders)
        self.assertIn("Main-Out ADAT3", panel.sliders)

        emitted_gains = {}
        panel.gain_changed.connect(lambda k, v: emitted_gains.update({k: v}))

        # Set initial level on Main-Out AN1/AN2
        slider = panel.sliders["Main-Out AN1/AN2"]
        slider.setValue(40000)
        self.assertEqual(emitted_gains.get("Main-Out AN1"), 40000)
        self.assertEqual(emitted_gains.get("Main-Out AN2"), 40000)

        # Mute Main-Out AN1/AN2
        mute_btn = panel.mute_buttons["Main-Out AN1/AN2"]
        mute_btn.setChecked(True)
        self.assertEqual(emitted_gains["Main-Out AN1"], 0)
        self.assertEqual(emitted_gains["Main-Out AN2"], 0)
        self.assertEqual(panel.pct_labels["Main-Out AN1/AN2"].text(), "0%")

        # Unmute restores level to both stereo channels
        mute_btn.setChecked(False)
        self.assertEqual(emitted_gains["Main-Out AN1"], 40000)
        self.assertEqual(emitted_gains["Main-Out AN2"], 40000)

        # Solo Main-Out AN1/AN2
        solo_btn = panel.solo_buttons["Main-Out AN1/AN2"]
        solo_btn.setChecked(True)
        self.assertEqual(emitted_gains["Main-Out AN1"], 40000)
        self.assertEqual(emitted_gains["Main-Out AN2"], 40000)

        solo_btn.setChecked(False)

    def test_single_instance_manager(self):
        test_server_name = f"pipewire_test_single_instance_{os.getpid()}"
        primary_mgr = SingleInstanceManager(server_name=test_server_name)
        
        # Initially, no server running
        self.assertFalse(primary_mgr.is_another_instance_running(timeout_ms=100))

        # Start primary server
        activated = []
        started = primary_mgr.start_server(lambda: activated.append(True))
        self.assertTrue(started)

        # Secondary instance should detect primary running and invoke activation
        secondary_mgr = SingleInstanceManager(server_name=test_server_name)
        self.assertTrue(secondary_mgr.is_another_instance_running(timeout_ms=500))

        # Process pending Qt events to trigger connection signal
        app.processEvents()
        self.assertEqual(len(activated), 1)

        # Clean up
        primary_mgr.close()
        self.assertFalse(secondary_mgr.is_another_instance_running(timeout_ms=100))

    def test_main_window_activate_to_front(self):
        window = MainWindow()
        if hasattr(window, 'detector') and window.detector:
            window.detector.wait(2000)
        window.activate_window_to_front()
        self.assertTrue(window.isVisible())
        window.close()


if __name__ == '__main__':
    unittest.main()
