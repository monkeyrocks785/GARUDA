"""Allow running as: python -m launcher"""

import sys

from launcher.cli import dispatch

if __name__ == "__main__":
    sys.exit(dispatch())
