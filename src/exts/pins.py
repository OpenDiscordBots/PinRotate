from datetime import datetime

from disnake import ApplicationCommandInteraction, TextChannel
from disnake.ext.commands import Cog, Param, has_guild_permissions, slash_command

from src.bot import Bot
from src.models import PinRotateConfig


class Pins(Cog):
    """The core logic for PinRotate."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self._cache: dict[int, PinRotateConfig] = {}

    async def get_config(self, guild_id: int) -> PinRotateConfig:
        if guild_id in self._cache:
            return self._cache[guild_id]

        config = (
            await self.bot.api.get_guild_config(guild_id, "pinrotate", PinRotateConfig)
        ) or PinRotateConfig(channels=[])

        self._cache[guild_id] = config

        return config

    async def set_config(self, guild_id: int, config: PinRotateConfig) -> None:
        await self.bot.api.set_guild_config(guild_id, "pinrotate", config.json())

        self._cache[guild_id] = config

    @slash_command(name="setup")
    @has_guild_permissions(manage_guild=True)
    async def setup(
        self,
        ctx: ApplicationCommandInteraction,
        channel: TextChannel = Param(desc="The channel to rotate pins in"),
    ) -> None:
        """Automatically remove old pins when needed to free space for new pins in a channel."""

        assert ctx.guild

        gconf = await self.get_config(ctx.guild.id)
        cid = str(channel.id)

        if cid in gconf.channels:
            await ctx.send(
                "That channel is already automatically rotated.", ephemeral=True
            )
            return

        gconf.channels.append(cid)

        await self.set_config(ctx.guild.id, gconf)

        await ctx.send(
            f"I will now automatically rotate pins in {channel.mention}",
            ephemeral=True,
        )

    @slash_command(name="unsetup")
    @has_guild_permissions(manage_guild=True)
    async def unsetup(
        self,
        ctx: ApplicationCommandInteraction,
        channel: TextChannel = Param(
            desc="The channel to no longer automatically publish messages in"
        ),
    ) -> None:
        """Stop automatically rotating pins for a channel."""

        assert ctx.guild

        gconf = await self.get_config(ctx.guild.id)
        cid = str(channel.id)

        if cid not in gconf.channels:
            await ctx.send(
                "That channel is not automatically rotated.", ephemeral=True
            )
            return

        gconf.channels.remove(cid)

        await self.set_config(ctx.guild.id, gconf)

        await ctx.send(
            f"I will no longer automatically rotate pins in {channel.mention}",
            ephemeral=True,
        )

    @Cog.listener()
    async def on_guild_channel_pins_update(self, channel: TextChannel, last_pin: datetime) -> None:
        gconf = await self.get_config(channel.guild.id)

        if not gconf.channels:
            return

        pins = await channel.pins()

        if len(pins) < 50:
            return

        await pins[-1].unpin()


def setup(bot: Bot) -> None:
    bot.add_cog(Pins(bot))
