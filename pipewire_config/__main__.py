"""Module entry point for python3 -m pipewire_config."""

import sys
from .ui.main_window import main

if __name__ == "__main__":
    sys.exit(main())
