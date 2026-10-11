"""The /random family — FUN-1.

Hot-path commands: short names, public replies, no ceremony. Failures reply
ephemerally so a mistake never becomes channel noise.
"""

from __future__ import annotations

import random
import re

import discord
from discord import app_commands
from discord.ext import commands

DICE = re.compile(r"^\s*(\d*)\s*[dD]\s*(\d+)\s*(?:([+-])\s*(\d+))?\s*$")

MAX_DICE = 100
MAX_SIDES = 1000

EIGHTBALL = (
    "It is certain.",
    "It is decidedly so.",
    "Without a doubt.",
    "Yes — definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very doubtful.",
)


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(description="Flip a coin")
    async def flip(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"\N{COIN} **{random.choice(('Heads', 'Tails'))}**"
        )

    @app_commands.command(description="Roll dice, e.g. 2d6+3")
    @app_commands.describe(dice="Standard notation: 1d20, 2d6+3, 4d8-1")
    async def roll(self, interaction: discord.Interaction, dice: str = "1d20") -> None:
        match = DICE.match(dice)
        if not match:
            await interaction.response.send_message(
                f"I can't read `{dice}`. Try something like `1d20`, `2d6+3` or `4d8-1`.",
                ephemeral=True,
            )
            return

        raw_count, raw_sides, sign, raw_mod = match.groups()
        count = int(raw_count) if raw_count else 1
        sides = int(raw_sides)
        modifier = 0
        if raw_mod:
            modifier = int(raw_mod) * (-1 if sign == "-" else 1)

        if not 1 <= count <= MAX_DICE:
            await interaction.response.send_message(
                f"Between 1 and {MAX_DICE} dice, please.", ephemeral=True
            )
            return
        if not 2 <= sides <= MAX_SIDES:
            await interaction.response.send_message(
                f"Dice need between 2 and {MAX_SIDES} sides.", ephemeral=True
            )
            return

        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier

        if count == 1 and not modifier:
            await interaction.response.send_message(
                f"\N{GAME DIE} `{dice.strip()}` \N{RIGHTWARDS ARROW} **{total}**"
            )
            return

        detail = " + ".join(str(r) for r in rolls)
        if modifier:
            detail += f" {'+' if modifier > 0 else '-'} {abs(modifier)}"
        await interaction.response.send_message(
            f"\N{GAME DIE} `{dice.strip()}` \N{RIGHTWARDS ARROW} {detail} = **{total}**"
        )

    @app_commands.command(name="8ball", description="Ask the magic 8-ball")
    @app_commands.describe(question="What do you want to know?")
    async def eightball(self, interaction: discord.Interaction, question: str) -> None:
        await interaction.response.send_message(
            f"\N{BILLIARDS} **{question}**\n{random.choice(EIGHTBALL)}"
        )

    @app_commands.command(description="Decide between options for us")
    @app_commands.describe(options="Comma-separated: pizza, curry, whatever")
    async def pick(self, interaction: discord.Interaction, options: str) -> None:
        choices = [o.strip() for o in options.split(",") if o.strip()]
        if len(choices) < 2:
            await interaction.response.send_message(
                "Give me at least two options, separated by commas.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"\N{THINKING FACE} **{random.choice(choices)}**"
        )

    @app_commands.command(description="Split your voice channel into teams")
    @app_commands.describe(count="How many teams (default 2)")
    async def teams(
        self,
        interaction: discord.Interaction,
        count: app_commands.Range[int, 2, 10] = 2,
    ) -> None:
        voice = getattr(interaction.user, "voice", None)
        if voice is None or voice.channel is None:
            await interaction.response.send_message(
                "Join a voice channel first — I split whoever's in there with you.",
                ephemeral=True,
            )
            return

        people = [m for m in voice.channel.members if not m.bot]
        if len(people) < count:
            await interaction.response.send_message(
                f"Only {len(people)} here, so I can't make {count} teams.",
                ephemeral=True,
            )
            return

        random.shuffle(people)
        # Round-robin, so team sizes never differ by more than one.
        buckets: list[list[discord.Member]] = [[] for _ in range(count)]
        for i, member in enumerate(people):
            buckets[i % count].append(member)

        # Mentions render as names and ping nobody: AllowedMentions.none() is a
        # client-wide default.
        lines = [
            f"**Team {i}** — " + ", ".join(m.mention for m in bucket)
            for i, bucket in enumerate(buckets, start=1)
        ]
        await interaction.response.send_message(
            f"\N{DIRECT HIT} **{voice.channel.name}**\n" + "\n".join(lines)
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
