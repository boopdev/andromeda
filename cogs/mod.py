import discord, asyncio, datetime, math
from discord.ext import commands
from utils import checks, butils, bconv

class ModerationCommands(commands.Cog, name="Moderation"):
    def __init__(self, client):
        self.client = client

    class warningObject():
        def __init__(self, _raw):
            self.id = _raw['warnid']
            self.userid = _raw['userid']
            self.modid = _raw['modid']
            self.reason = _raw['reason']
            self.timestamp = _raw['warned']

    async def create_warning(self, user : discord.User, mod : discord.User, reason : str):
        t = datetime.datetime.utcnow()
        await self.client.db.execute(
            "INSERT INTO warnings(userid, modid, reason, warned) VALUES ($1, $2, $3, $4);",
            user.id, mod.id, reason, t
        )
        r = await self.client.db.fetchrow(
            "SELECT * FROM warnings WHERE warned=$1 AND modid=$2", t, mod.id
        )
        return self.warningObject(r)

    async def get_warning(self, _id : int):
        w=await self.client.db.fetchrow(
            "SELECT * FROM warnings WHERE warnid=$1", _id
        )
        if w in ((),[],None): return None
        return self.warningObject(w)

    async def get_user_warnings(self, user : discord.User):
        w = await self.client.db.fetchall(
            "SELECT * FROM warnings WHERE userid=$1", user.id
        )
        return [self.warningObject(x) for x in w]

    async def delete_warning(self, _id : int):
        await self.client.db.execute("DELETE FROM warnings WHERE warnid=$1", _id)

    @checks.require_rank('intern')
    @commands.command()
    async def warn(self, ctx, user : discord.Member, *, reason : str):
        """Warn a user"""
        await ctx.message.delete()
        z=await self.create_warning(
            user=user,
            mod=ctx.author,
            reason=reason
        )
        return await ctx.send(
            embed = butils.Embed(
                description = f"**Warning ID:** `{hex(z.id)[2:].upper()}`"
            ).add_field(
                name = "Reason",
                value = f"```\n{reason}```"
            ).set_author(
                name = f"{user} was warned!", icon_url = user.avatar_url
            )
        )

    @checks.require_rank('mod')
    @commands.command()
    async def delwarn(self, ctx, warnid : bconv.HexConverter):
        """Delete a warn based on its warn id"""
        check = await self.get_warning(warnid)
        if check == None: return await ctx.send(
            "> ❌ | {ctx.author.mention} `No warning with the specified id exists`"
        )
        await self.delete_warning(warnid)
        return await ctx.send(
            embed = butils.Embed(
                description = f"Deleted Warning `{hex(warnid)[2:].upper()}`!"
                ,colour = self.client._colours['yes']
            )
        )

    @checks.require_rank('intern')
    @commands.command(aliases=['warnings'])
    async def warns(self, ctx, *, user : discord.User, pg : int = 0):
        """View all warns from a user"""

    @checks.require_rank('intern')
    @commands.command(aliases=['bc'])
    async def botclear(self, ctx):
        """Clears all bot responses"""
        await ctx.message.delete()

        if self.client._config['bc-clean-prefixes']: # If the bot should check for prefix messages too
            deleted = await ctx.channel.purge(
                limit = self.client._config['bc-safety-limit'],
                check = lambda m: any([m.content.startswith(x) for x in self.client._config['bc-prefixes']]) or m.author.bot
            )
        else:
            deleted = await ctx.channel.purge(
                limit = self.client._config['bc-safety-limit'],
                check = lambda m: m.author.bot
            )
        
        return await ctx.send(
            embed = butils.Embed(
                colour = self.client._colours['yes'],
                description = f"**Purged `{len(deleted):,}` Messages**"
            ).set_footer(
                text = str(ctx.author), icon_url = ctx.author.avatar_url
            ),
            delete_after=4
        )

def setup(client):
    client.add_cog(
        ModerationCommands(client=client)
    )