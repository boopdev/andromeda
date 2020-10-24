import discord, asyncio, humanize, datetime
from discord.ext import commands
from utils import butils

class GeneralCommands(commands.Cog, name="General"):
    def __init__(self, client):
        self.client = client

    async def get_afks(self):
        return await self.client.db.fetch("SELECT * FROM afk;")

    @commands.Cog.listener('on_message')
    async def afk_listener(self, message):
        if message.author.bot: return # Disallow Bot Pings to Trigger AFK
        afks = await self.get_afks()

        # Check for author message first
        if message.author.id in [z['userid'] for z in afks]:

            x = [z for z in afks if z['userid'] == message.author.id][0]
            if x['afkat'] + datetime.timedelta(seconds=5) > datetime.datetime.utcnow():
                return # 1 Minute delay before unset


            await self.unset_afk(message.author)
            return await message.channel.send(
                    f"> {message.author.mention}",
                    embed = butils.Embed(
                        colour = message.author.colour if message.author.colour.value != 0 else self.client._colours['default']
                    ).set_author(
                        name = f"Welcome back {message.author.display_name}", icon_url = message.author.avatar_url
                    )
                )
        
        # Check for mentions now
        z=filter(lambda q: q['userid'] in [i.id for i in message.mentions], afks)
        z = list(z)
        if len(z) == 1:
            afk_user = await self.client.fetch_user(z[0]['userid'])
            return await message.channel.send(
                f"> {message.author.mention}",
                embed = butils.Embed(
                    title = f"{afk_user.display_name} is AFK!",
                    description = f"> {z[0]['message']}"
                )
            )


    async def unset_afk(self, user : discord.User):
        await self.client.db.execute("DELETE FROM afk WHERE userid=$1", user.id)

    async def set_afk(self, user : discord.User, reason : str, update:bool=False):
        if not update:
            await self.client.db.execute('INSERT INTO afk VALUES ($1, $2, CURRENT_TIMESTAMP)', user.id, reason)
        else:
            await self.client.db.execute('UPDATE afk SET message=$1, afkat=CURRENT_TIMESTAMP WHERE userid=$2', reason, user.id)

    @commands.command()
    async def afk(self, ctx, *, reason : str = None):
        """Sets a user's afk message, when the user gets a ping it will notify the pinger of their absence"""
        afkch = await self.client.db.fetchrow("SELECT * FROM afk WHERE userid=$1", ctx.author.id)
        if afkch: # If the user exists within da database
            if reason is None:
                await self.unset_afk(ctx.author)
                return await ctx.send(
                    f"> {ctx.author.mention}",
                    embed = butils.Embed(
                        colour = ctx.author.colour if ctx.author.colour.value != 0 else self.client._colours['default']
                    ).set_author(
                        name = f"Welcome back {ctx.author.display_name}", icon_url = ctx.author.avatar_url
                    )
                )
            else: # If the reason is provided
                await self.set_afk(ctx.author, reason = reason, update = True)
                return await ctx.message.add_reaction("✅")
        await self.set_afk(ctx.author, reason = reason, update = False)
        return await ctx.send(
            embed = butils.Embed(
                description = f"**__Reason__**\n> *{reason}*",
                colour = ctx.author.colour if ctx.author.colour.value != 0 else self.client._colours['default']
            ).set_author(
                name = f"{ctx.author.display_name} is now AFK", icon_url = ctx.author.avatar_url
            )
        )


def setup(client):
    client.add_cog(
        GeneralCommands(client)
    )

