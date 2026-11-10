#!/usr/bin/env python3
"""
PipeWire Audio Device Configuration GUI
Backward-compatible wrapper script forwarding to pipewire_config package.
"""

import sys
from pipewire_config.ui.main_window import main

if __name__ == "__main__":
    sys.exit(main())
