import discord, asyncio
from discord.ext import commands
from utils import bconv, butils

class GamblingCog(commands.Cog, name="Gambling"):
    def __init_(self, client):
        self.client = client

        self.eco = lambda: client.get_cog("Economy")

    @commands.command()
    async def gamble(self, ctx, *, amount : bconv.AdvancedIntConverter):
        """spend your welfare check money here"""
        _ub = await self.eco.get_balance(ctx.author)
        if not _ub.cash >= amount: 
            return await ctx.send(
                f"> {ctx.author.mention}",
                embed = self.client.get_cog("Errors")._unified_error_format(
                    "You don't have enough cash on your to bet that much!",
                    title = None,
                    show_help = False
                )
            )