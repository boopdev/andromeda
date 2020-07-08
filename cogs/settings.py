import discord, asyncio
from discord.ext import commands

class Settings(commands.Cog):
    def __init__(self, client):
        self.client = client

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

def setup(client): client.add_cog(Settings(client))