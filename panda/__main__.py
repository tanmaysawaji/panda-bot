"""Entry point: `python -m panda`."""

from __future__ import annotations

import sys

from .config import ConfigError, load
from .main import run


def cli() -> int:
    try:
        config = load()
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    run(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
