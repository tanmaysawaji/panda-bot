"""Client construction and startup."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from . import __version__
from .config import Config

log = logging.getLogger(__name__)

EXTENSIONS = (
    "panda.commands.meta",
    "panda.commands.fun",
)


def _intents() -> discord.Intents:
    """Exactly the intents Panda uses, and no others.

    `members` is privileged and must be enabled in the developer portal. It is
    not optional: VoiceChannel.members resolves each voice state through the
    member cache and silently skips anyone missing from it, and GUILD_CREATE
    does not populate that cache without it. Everyone already sitting in voice
    when Panda boots would be invisible — which breaks /teams today and
    "disconnect when the last human leaves" later.
    """
    intents = discord.Intents.none()
    intents.guilds = True
    intents.voice_states = True
    intents.members = True
    return intents


class Panda(commands.Bot):
    def __init__(self, config: Config) -> None:
        self.config = config
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=_intents(),
            # Non-negotiable. Testing happens live on the real server, and this
            # is what makes that safe: the bot becomes structurally incapable of
            # pinging anyone, including an @everyone inside text it echoes back.
            allowed_mentions=discord.AllowedMentions.none(),
            help_command=None,
            activity=discord.Game(name="/panda"),
        )

    @property
    def guild(self) -> discord.Object:
        return discord.Object(id=self.config.guild_id)

    async def setup_hook(self) -> None:
        for ext in EXTENSIONS:
            await self.load_extension(ext)
            log.debug("loaded extension %s", ext)

        # Guild-scoped rather than global: commands appear instantly instead of
        # taking up to an hour to propagate.
        self.tree.copy_global_to(guild=self.guild)
        synced = await self.tree.sync(guild=self.guild)
        log.info(
            "synced %d command(s) to guild %d: %s",
            len(synced),
            self.config.guild_id,
            ", ".join(sorted(c.name for c in synced)) or "none",
        )

    async def on_ready(self) -> None:
        assert self.user is not None
        log.info("Panda %s is up as %s (%d)", __version__, self.user, self.user.id)


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # discord.py is chatty about the gateway at INFO.
    logging.getLogger("discord").setLevel(logging.WARNING)


def run(config: Config) -> None:
    _setup_logging(config.log_level)
    Panda(config).run(config.token, log_handler=None)
