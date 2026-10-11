"""Configuration, read from the environment.

Every value Panda needs is read once at startup and validated there, so a
missing or malformed setting is a clear message at boot rather than an
AttributeError twenty minutes later.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigError(Exception):
    """Raised when the environment is missing or malformed."""


@dataclass(frozen=True)
class Config:
    token: str
    guild_id: int
    log_level: str


def load() -> Config:
    """Read configuration from .env and the process environment.

    Real environment variables win over .env, which is what lets systemd
    supply the production values without a file sitting next to the code.
    """
    load_dotenv(override=False)

    problems: list[str] = []

    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        problems.append("DISCORD_TOKEN is not set")

    raw_guild = os.getenv("GUILD_ID", "").strip()
    guild_id = 0
    if not raw_guild:
        problems.append("GUILD_ID is not set")
    else:
        try:
            guild_id = int(raw_guild)
        except ValueError:
            problems.append(f"GUILD_ID must be a number, got {raw_guild!r}")

    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    if problems:
        raise ConfigError(
            "Configuration is incomplete:\n"
            + "\n".join(f"  - {p}" for p in problems)
            + "\n\nCopy .env.example to .env and fill it in."
        )

    return Config(token=token, guild_id=guild_id, log_level=log_level)
