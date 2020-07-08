import discord, asyncio, aiohttp, random, math
from discord.ext import commands
from utils import butils
from utils.smartCD import CooldownType, smart_cooldown, CommandOnCooldown

class FunCommands(commands.Cog, name='Fun'):
    def __init__(self, client):
        self.client = client

    @commands.command(name='bored')
    async def _bored(self, ctx):
        """Bored? Here's something you can do besides wasting our fucking air"""
        async with aiohttp.ClientSession() as s:
            async with s.get('https://www.boredapi.com/api/activity') as resp:
                r = await resp.json(encoding='utf-8')

        return await ctx.send(
            content=f"> {ctx.author.mention} Here's an activity you can do lazy ass bitch",
            embed = butils.Embed(
                description = f"> [🔗 Click here for a Link!]({r['link']})" if r['link'] not in ("",None) else discord.Embed.Empty
            ).set_author(
                name = str(r['activity']), icon_url=ctx.author.avatar_url
            )
        )

    async def _register_cookies(self, user : discord.User):
        await self.client.db.execute("INSERT INTO cookies VALUES ($1, 0, 0);", user.id)
        return {"userid" : user.id, "given" : 0, 'recieved' : 0}

    async def _get_cookies(self, user : discord.User):
        q = await self.client.db.fetchrow("SELECT * FROM cookies WHERE userid=$1", user.id)
        if q is None:
            return await self._register_cookies(user)
        return q

    # http://cheems.boopsu.ga/owo/c6l.png <-- Cookie pic
    @smart_cooldown(3600, CooldownType.user)
    @commands.group(name="cookie", invoke_without_command=True)
    async def _cookie(self, ctx, *, user : discord.Member):
        """Give cookies and give them to your friends!"""
        if user == ctx.author: return await ctx.send(
            embed = butils.Embed(
                colour=self.client._colours['no'],
            ).set_author(
                name = "Share your cookies twat", icon_url = ctx.author.avatar_url
            )
        )
        q=await self._get_cookies(user)
        await self._get_cookies(ctx.author)
        await self.client.db.execute("UPDATE cookies SET given=given+1 WHERE userid=$1;", ctx.author.id)
        await self.client.db.execute("UPDATE cookies SET recieved=recieved+1 WHERE userid=$1;", user.id)
        return await ctx.send(
            content=f"> {user.mention}",
            embed = butils.Embed(
                colour=self.client._colours['yes'],
                description=f"🍪 {user.mention} now has `{q['recieved']+1:,}` cookies!"
            ).set_thumbnail(
                url="http://cheems.boopsu.ga/owo/c6l.png"
            ).set_author(
                name = f"{ctx.author.display_name} gave {user.display_name} a cookie!",
                icon_url = ctx.author.avatar_url
            )
        )

    @_cookie.command(name='leaderboard', aliases=['lb'])
    async def cookie_leaderboard(self, ctx):
        """Who got da most cookies??"""
        recieved = await self.client.db.fetch(
            "SELECT * FROM cookies ORDER BY recieved DESC LIMIT 15;"
        )
        given = await self.client.db.fetch(
            "SELECT * FROM cookies ORDER BY given DESC LIMIT 15;"
        )
        _r, _g = {}, {}
        for i in recieved:
            if len(_r) >= 5: break
            u=self.client.scarlyst.get_member(i['userid'])
            _r[u] = i['recieved']

        for i in given:
            if len(_g) >= 5: break
            u=self.client.scarlyst.get_member(i['userid'])
            _g[u] = i['given']

        return await ctx.send(
            embed = butils.Embed(
                
            ).set_thumbnail(
                url = "http://cheems.boopsu.ga/owo/c6l.png"
            ).add_field(
                name = "Cookies Received", value = "\n".join(
                    [
                        f"`{i}` **{x}** `{_r[x]:,} 🍪`" for i, x in enumerate(_r, start=1)
                    ]
                ),
                inline=False
            ).add_field(
                name = "Cookies Given", value = "\n".join(
                    [
                        f"`{i}` **{x}** `{_g[x]:,} 🍪`" for i, x in enumerate(_g, start=1)
                    ]
                ),
                inline=False
            )
        )

    @_cookie.error
    async def cookie_errors(self, ctx, error):
        if isinstance(error, CommandOnCooldown):
            return await ctx.send(
                content=f"> {ctx.author.mention}",
                embed = butils.Embed(
                    description=f"<:PepeSadHugS:648215659133534213> We know your bitchass wants to give out more cookies but fuck you. you gotta wait for {error.humanize}",
                    colour=self.client._colours['no']
                )
            )
        else:
            # Resets cooldown incase of a command fuck up
            await self.client.db.execute(
                "DELETE FROM smartcd WHERE userid=$1 AND cmd=$2",
                ctx.author.id, ctx.command.qualified_name
            )
            return await self.client.get_cog("Errors")._handle_errors(ctx, error, fallback=True)

    @commands.command(name="ship", aliases=['lovecalc', 'love'])
    async def _ship(self, ctx, user_a : discord.Member, user_b : discord.Member = None):
        """Aww shipping is so fun and quirky!!!"""
        if user_b is None:
            user_b, user_a = user_a, ctx.author
        perc = random.uniform(0,100)
        return await ctx.send(
            embed = butils.Embed(
                colour=butils.intensify_colour(self.client._colours['love'], round(perc)),
                description="`[{0}]` `({1}%)`".format(butils.progress_bar(progress=perc, _max=100, max_columns=15, col_empty='▁'), round(perc, 1))
            ).set_author(
                name = user_a.display_name, icon_url=user_a.avatar_url
            ).set_footer(
                text = user_b.display_name, icon_url = user_b.avatar_url
            )
        )

    class userCock:
        def __init__(self, *args, **kwargs):
            self.userid = kwargs.get('userid', -1)
            self.length = kwargs.get('length', 0)
            self.sfwon = kwargs.get('sfwon', 0)
            self.sflost = kwargs.get('sflost', 0)
            self.prestige = kwargs.get('prestige', 0)

        @property
        def wlratio(self): return self.sfwon / self.sflost

        @property
        def sftotal(self): return self.sfwon + self.sflost

    async def create_cock_data(self, user : discord.User):
        await self.client.db.execute(
            "INSERT INTO penises VALUES ($1, $2, 0, 0, 0);",
            user.id, random.uniform(
                self.client._config['pp-length-min'], self.client._config['pp-length-max']
            )
        )
        f = await self.client.db.fetchrow("SELECT * FROM penises WHERE userid=$1", user.id)
        return self.userCock(**f)

    async def get_user_cock(self, user : discord.User):
        _r = await self.client.db.fetchrow("SELECT * FROM penises WHERE userid=$1", user.id)
        if _r is None:
            return await self.create_cock_data(user)
        return self.userCock(**_r)


    @commands.group(aliases=['pp', 'cock', 'dick'], invoke_without_command=True)
    async def penis(self, ctx, user : discord.Member = None):
        """Measure your cock"""
        if user is None: user = ctx.author
        _ucock = await self.get_user_cock(user)
        return await ctx.send(
            embed = butils.Embed(
                title = f"8{'='*math.floor(_ucock.length) if not _ucock.length>100 else '='*100}D",
            ).set_author(
                name = f"{user.display_name}'s penis ({round(_ucock.length, 2)}in.)",
                icon_url = user.avatar_url
            ).add_field(
                name = "Swordfight Statistics",
                value = f"""
                Wins: `{_ucock.sfwon:,}`
                Losses: `{_ucock.sflost:,}`
                Total Fights: `{_ucock.sftotal:,}`
                W/L Ratio: `{_ucock.sftotal:,}`
                """
            ).set_thumbnail(
                url = user.avatar_url
            )
        )

    @smart_cooldown(300)
    @commands.command()
    async def swordfight(self, ctx, user : discord.Member):
        """Swing your 'swords' at eachother, whoever wins gets more cock!"""


def setup(client):
    client.add_cog(FunCommands(client))