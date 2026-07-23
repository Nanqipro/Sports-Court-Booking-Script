"""Compatibility entry point for users who prefer running a script file."""

from ncu_booking.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

