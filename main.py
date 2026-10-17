"""Launch Fly-in from the repository root."""
import sys

from fly_in.application import Application


if __name__ == '__main__':
    sys.exit(Application().run())
