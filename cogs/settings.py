import discord, asyncio
from discord.ext import commands
from utils import checks

class Settings(commands.Cog):
    def __init__(self, client):
        self.client = client

    class IgnoredChannel(commands.CheckFailure):
        pass

    async def cache_autoroles(self):
        if not hasattr(self, 'autorole_data') or len(self.autorole_data) != len(self.client._config['autoroles']):
            p = await self.get_autoroles()
            self.__setattr__('autorole_data', p)
        return self.autorole_data

    async def get_autoroles(self):
        pp = []
        for i in self.client._config['autoroles']:
            u = self.client.scarlyst.get_role(i)
            pp.append(u)
        return pp

    @commands.Cog.listener('on_member_join')
    async def autorole_bullshit(self, member):
        if not self.client._config['autorole-bots'] and member.bot: return

        roles = await self.cache_autoroles()
        for r in roles:
            if not any([r == ur for ur in member.roles]):
                await member.add_roles(r)
        return

    # This is the ignore check
    async def bot_check(self, ctx):

        # Mods have bypass
        try:
            is_mod = await checks.require_rank('mod').predicate(ctx, noerror=True)
        except:
            pass
        else:
            if is_mod: return True

        # The actual shizzle
        _r = await self.client.db.fetch("SELECT * FROM ignores;")
        if ctx.channel.id not in [i['channelid'] for i in _r]:
            return True
        else:
            raise self.IgnoredChannel() # So we can silently handle this error :)

    @checks.require_rank('admin')
    @commands.guild_only()
    @commands.command()
    async def ignore(self, ctx, channel : discord.TextChannel = None):
        """Ignores commands in a channel"""
        if channel is None: channel = ctx.channel

        double_check = await self.client.db.fetchrow("SELECT * FROM ignores WHERE channelid=$1", channel.id)
        if double_check is not None:
            return await ctx.send(
                f"> {channel.mention} is already being ignored..."
            )

        await self.client.db.execute(
            "INSERT INTO ignores VALUES ($1)", channel.id 
        )

        return await ctx.send(
            f"> Members can no longer use commands in {channel.mention}"
        )

    @checks.require_rank('admin')
    @commands.guild_only()
    @commands.command()
    async def listen(self, ctx, channel : discord.TextChannel = None):
        """Basically the same thing as ignore but reversed"""
        if channel is None:
            channel = ctx.channel

        double_check = await self.client.db.fetchrow(
            "SELECT * FROM ignores WHERE channelid=$1", channel.id
        )
        if double_check is None:
            return await ctx.send(
                f"> {channel.mention} is not being ignored."
            )

        await self.client.db.execute("DELETE FROM ignores WHERE channelid=$1", channel.id)

        return await ctx.send(
            f"> Members can now use commands in {channel.mention}"
        )



def setup(client): client.add_cog(Settings(client))