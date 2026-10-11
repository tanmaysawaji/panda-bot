"""/panda — the help and command reference (UTIL-10).

Generated from the registered command tree, never hand-written. Hand-written
docs drift the moment a command changes; generated ones cannot.

Named /panda rather than /help because other bots on the server already claim
the common names, and typing the bot's name to find out what it does is the
most discoverable thing available.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from .. import __version__


def _signature(command: app_commands.Command) -> str:
    """Render a command as `/name <required> [optional]`."""
    parts = [f"/{command.qualified_name}"]
    for param in command.parameters:
        parts.append(
            f"<{param.display_name}>" if param.required else f"[{param.display_name}]"
        )
    return " ".join(parts)


def _visible(
    commands_: list[app_commands.Command | app_commands.Group],
) -> list[app_commands.Command]:
    """Flatten groups into their subcommands, dropping anything admin-only.

    A command opts out of the public listing with
    `@app_commands.command(..., extras={"admin": True})`.
    """
    found: list[app_commands.Command] = []
    for item in commands_:
        if item.extras.get("admin"):
            continue
        if isinstance(item, app_commands.Group):
            found.extend(_visible(list(item.commands)))
        else:
            found.append(item)
    return found


class Meta(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(description="What Panda can do")
    async def panda(self, interaction: discord.Interaction) -> None:
        registered = list(self.bot.tree.get_commands(guild=interaction.guild))
        if not registered:
            registered = list(self.bot.tree.get_commands())

        listing = sorted(_visible(registered), key=lambda c: c.qualified_name)

        embed = discord.Embed(
            title="Panda",
            description="Everything I answer to. Only you can see this.",
            colour=discord.Colour.from_str("#2b2d31"),
        )
        for command in listing:
            embed.add_field(
                name=_signature(command),
                value=command.description or "\u2014",
                inline=False,
            )
        embed.set_footer(text=f"v{__version__}")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Meta(bot))
