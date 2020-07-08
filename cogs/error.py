import discord
import asyncio
from discord.ext import commands

from utils.smartCD import CommandOnCooldown
from utils.checks import MissingRequiredRank

class ErrorHandling(commands.Cog, name="Errors"):
    def __init__(self, client):
        self.client = client

    # This is like the boilerplate for error messages, you should edit this if you wanna change the look of it
    def _unified_error_format(self, ctx, txt : str, show_help:bool=True, title:str="We got an error chief"):
        return discord.Embed(
            title=title if title != None else discord.Embed.Empty,
            colour=self.client._colours['no'],
            description=f"> {txt}\n\n" + ("" if not show_help else f"**Command Usage:** `{ctx.prefix}{ctx.invoked_with} {ctx.command.signature}`")
        ).set_author(
            name = f"{ctx.author.display_name}", icon_url = ctx.author.avatar_url
        )

    async def _handle_errors(self, ctx, error, *, fallback : bool = False):
        if not fallback:
            if hasattr(ctx.command, 'on_error'):
                return # No error plz

        if isinstance(error, CommandOnCooldown):
            return None # All of these should have their own errors, right?
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(embed=self._unified_error_format(ctx,f"You're missing the argument `{str(error.param).split(':')[0]}` which is a required argument for this command."))
        elif isinstance(error, (commands.BadArgument, commands.BadUnionArgument)):
            return await ctx.send(
                embed=self._unified_error_format(ctx,
                    f"{error.message}" if isinstance(error, commands.BadArgument) else f"{error.args[0]}"
                )
            )
        elif isinstance(error, MissingRequiredRank):
            return await ctx.send(
                embed = self._unified_error_format(
                    ctx,
                    f"You need to be a **{error.rank_title.title()}** to use this command!",
                    show_help=False,
                    title = discord.Embed.Empty
                )
            )
        else:
            raise error

    @commands.Cog.listener("on_command_error")
    async def HANDLE_MY_ERRORS_FUCKNUTS(self, ctx, error):
        return await self._handle_errors(ctx, error)
        

def setup(client):
    client.add_cog(ErrorHandling(client))