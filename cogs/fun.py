import discord, asyncio, aiohttp, random, math, datetime, humanize
from discord.ext import commands
from utils import butils, butilsImg
from utils.smartCD import CooldownType, smart_cooldown, CommandOnCooldown

_NEKOS_API_ENDPOINT = "https://nekos.life/api/v2"

class FunCommands(commands.Cog, name='Fun'):
    def __init__(self, client):
        self.client = client

        self._kill_weapons = [
            "a fish", "a spoon", "a gun", "their massive cock",
            "a gigantic breadstick", "excalibur", "a big axe",
            "many, many fire ants", "a cheap dollarstore squirt gun",
            "a cactus", "their little pansy fingers", "a stethoscope?",
            "their nagging", "their bitching", "their sarcastic overtones",
            "help from nobody other than the infamous Obama", "black power",
            "afterbirth", "cum, bucketloads of cum", 'their "yogurt"'
        ]

        # (user) [_kill_adj] (dead dude) with [_kill_wpn].

        self._kill_adjectives = [
            "brutally murdered", "destroyed", "killed",
            "plucked out the eyes of", "bashed in the skull of",
            "ruptured the anus of", "exploded", "imploded",
            "beat the shit out of", "annihilated", "murded 4 important people and",
            "accidentally ended the life of"
        ]

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
            u=await self.client.fetch_user(i['userid'])
            if i['recieved'] > 0:
                _r[u] = i['recieved']
            if len(_r) >= 5: break

        for i in given:
            u=await self.client.fetch_user(i['userid'])
            if i['given'] > 0:
                _g[u] = i['given']
            if len(_g) >= 5: break

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
            ).set_thumbnail(
                url = self.client.scarlyst.icon_url
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

    async def is_user_married(self, user : discord.Member):
        x = await self.client.db.fetchrow(
            "SELECT * FROM marriages WHERE usera = $1 OR userb = $1", user.id
        )
        return x

    async def marry_these_hoes(self, usera : discord.User, userb : discord.User):
        a, b = sorted([usera, userb,], key = lambda u: u.id) # Sort by ID because sex
        await self.client.db.execute(
            "INSERT INTO marriages VALUES ($1, $2, CURRENT_TIMESTAMP);",
            a.id, b.id
        )

    @commands.command()
    async def marry(self, ctx, u : discord.Member):
        """Marry a bitch"""
        if u == ctx.author:
            return await ctx.send(
                f"{ctx.author.mention}... Self-cest, really? You cant marry yourself you lonely fuck, go get some mad bitches like me -boop"
            )

        if u.bot:
            return await ctx.send(
                f"{ctx.author.mention}... You cant marry a robot, that's a little too kinky."
            )


        author_married = await self.is_user_married(ctx.author)

        if author_married is not None:
            am2w = author_married['usera'] if author_married['usera'] != ctx.author.id else author_married['userb']
            am2w = await self.client.fetch_user(am2w)
            return await ctx.send(
                f"> {ctx.author.mention}",
                embed = butils.Embed(
                    colour = self.client._colours['no'],
                    description = f"Sorry pal, you're already simping **{am2w}**!"
                ).set_author(
                    name = "Uh oh!", icon_url = ctx.author.avatar_url
                )
            )

        user_married = await self.is_user_married(u)

        if user_married is not None:
            um2w = user_married['usera'] if user_married['usera'] != u.id else user_married['userb']
            um2w = await self.client.fetch_user(um2w)
            return await ctx.send(
                f"> {ctx.author.mention}",
                embed = butils.Embed(
                    colour = self.client._colours['no'],
                    description = f"Sorry pal, you're already simping **{um2w}**!"
                ).set_author(
                    name = "Uh oh!", icon_url = ctx.author.avatar_url
                )
            )            

        m = await ctx.send(
            f"> {u.mention}",
            embed = butils.Embed(
                colour = self.client._colours['love'],
                description = f"{ctx.author.mention} is proposing to you, do you accept?"
            ).set_footer(
                text = "Yes and No are the only options.",
                icon_url = self.client.user.avatar_url
            ).set_author(
                name = f"😳 yo {u.display_name.lower()}"
            )
        )

        try:
            bruh = await self.client.wait_for(
                'message',
                check = lambda x : x.author.id == u.id and x.channel == ctx.channel and x.content.lower() in ('yes', 'no', 'accept', 'cancel'),
                timeout = 30
            )
        except asyncio.TimeoutError:
            return await m.edit(
                content = f"{u.display_name} took too long... ",
                embed = None
            )
        else:
            if bruh.content.lower() not in ('no', 'cancel'):
                await self.marry_these_hoes(ctx.author, u)


                return await ctx.send(
                    embed = butils.Embed(
                        colour = self.client._colours['love'],
                        description = f"**Congratulations** {ctx.author.display_name} and {u.display_name} are now officially e-married!"
                    ).set_footer(
                        text = "Imagine only being able to get discord bitches... lol virgins."
                    )
                )
            return await ctx.send(f"Damn {ctx.author.mention} you got rejected?... guess you're a virgin on discord and irl... lame bro..")

    @commands.command(aliases=['marriedto',])
    async def married(self, ctx, u : discord.User = None):
        """Check who a user is married to"""

        if u is None:
            u = ctx.author
        
        m = await self.is_user_married(u)

        if m is None:
            if u != ctx.author:
                return await ctx.send(
                    f"> {ctx.author.mention}",
                    embed = butils.Embed(
                        colour = self.client._colours['grey'],
                        description = f"{u.mention} is not married... it's time to shoot your shot 😳"
                    )
                )
            else:
                return await ctx.send(
                    f"> {ctx.author.mention}",
                    embed = butils.Embed(
                        colour = self.client._colours['grey'],
                        description = "You aren't married to anybody. :("
                    )
                )

        uobj = await self.client.fetch_user(
            m['usera'] if m['usera'] != u.id else m['userb']
        )

        time_passed = datetime.datetime.utcnow() - m['marriedat']
        humanized = humanize.naturaldelta(time_passed)

        f = await butilsImg.make_progress_bar(
            self.client, 
            time_passed.days,
            _max = 90,
            color = self.client._colours['love']
        )

        return await ctx.send(
            embed = butils.Embed(
                colour = self.client._colours['love'],
                description = f"**{u}** is married to **{uobj}**\n\nThey've been married for **{humanized}**!"
            ).set_image(
                url = 'attachment://progressbar.jpeg'
            ),
            file = f
        )

    @commands.command()
    async def divorce(self, ctx):
        """Divorice the user youre married to"""
        
        q = await self.is_user_married(ctx.author)

        if q is None:
            return await ctx.send(
                f"> {ctx.author.mention}",
                embed = butils.Embed(
                    description = "You're not married? You can't divorce somebody without being married lol.",
                    colour = self.client._colours['no']
                ).set_author(
                    name = "lmao wtf", icon_url = ctx.author.avatar_url
                )
            )
        
        await self.client.db.execute(
            "DELETE FROM marriages WHERE usera=$1 OR userb=$1", ctx.author.id
        )

        was_married_to = q['usera'] if q['usera'] != ctx.author else q['userb']
        was_married_to = await self.client.fetch_user(was_married_to)

        return await ctx.send(
            embed = butils.Embed(
                description = f"{ctx.author.mention} divorced {was_married_to}! Guess it was for the best"
            ).set_author(
                name = "Things didnt work out...", icon_url = ctx.author.avatar_url
            )
        )


    class userCock:
        def __init__(self, *args, **kwargs):
            self.user = kwargs.get('user', None)
            self.userid = kwargs.get('userid', -1)
            self.length = kwargs.get('length', 0)
            self.sfwon = kwargs.get('sfwon', 0)
            self.sflost = kwargs.get('sflost', 0)
            self.prestige = kwargs.get('prestige', 0)

        @property
        def wlratio(self):
            if self.sfwon != 0 and self.sflost == 0:
                return self.sfwon
            elif self.sfwon == 0 and self.sflost != 0:
                return 0
            elif self.sftotal == 0:
                return 0
            return self.sfwon / self.sflost

        @property
        def sftotal(self): return self.sfwon + self.sflost

        @property # Cock Length + Prestige Bonus
        def rlength(self): return self.length + (self.prestige * 3)

    async def create_cock_data(self, user : discord.Member):
        await self.client.db.execute(
            "INSERT INTO penises VALUES ($1, $2, 0, 0, 0);",
            user.id, random.uniform(
                self.client._config['pp-length-min'], self.client._config['pp-length-max']
            )
        )
        f = await self.client.db.fetchrow("SELECT * FROM penises WHERE userid=$1", user.id)
        return self.userCock(user=user, **f)

    async def get_user_cock(self, user : discord.Member):
        _r = await self.client.db.fetchrow("SELECT * FROM penises WHERE userid=$1", user.id)
        if _r is None:
            return await self.create_cock_data(user)
        return self.userCock(user=user, **_r)


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
                W/L Ratio: `{_ucock.wlratio:,}`
                """
            ).set_thumbnail(
                url = user.avatar_url
            )
        )

    async def swordfight_win(self, winner : userCock, loser : userCock):
        winnings = loser.length * round(random.uniform(0.1, 0.3), 1)
        winnings = winnings if winnings > 0 else 0 # Prevent negatives

        print(winner, loser, sep='\t')

        # Remove loser's penis
        await self.client.db.execute(
            'UPDATE penises SET length=length-$1, sflost=sflost+1 WHERE userid=$2', winnings, loser.userid
        )

        await self.client.db.execute(
            "UPDATE penises SET length=length+$1, sfwon=sfwon+1 WHERE userid=$2", winnings, winner.userid
        )

        return winnings

    @smart_cooldown(300, CooldownType.user)
    @commands.command(aliases=['sf',])
    async def swordfight(self, ctx, user : discord.Member):
        """Swing your 'swords' at eachother, whoever wins gets more cock!"""

        if user == ctx.author:
            await ctx.send(f"{ctx.author.mention}... you're retarded, aren't you..?")
            raise commands.BadArgument()

        elif user.bot:
            await ctx.send(
                f"{ctx.author.mention}... you can't swordfight bots man, that's just weird."
            )
            raise commands.BadArgument()

        callum_has_a_large_cock = await ctx.send(
            f"> {user.mention}",
            embed = butils.Embed(
                description = f"{ctx.author.mention} has challenged you to a cockfight! Do you accept?"
            ).set_author(
                name = "You've been challenged!", icon_url = user.avatar_url
            ).set_footer(
                text = "Type yes or no"
            )
        )

        try:
            jess_cant_rap = await self.client.wait_for(
                'message',
                check = lambda x: x.author == user and x.content.lower() in ('yes', 'no', 'agree', 'deny'),
                timeout = 30
            )
        except asyncio.TimeoutError:
            await callum_has_a_large_cock.delete()
            return await ctx.send(
                f"Seems like {user.display_name} was too chicken to answer in time..."
            )
        else:
            await callum_has_a_large_cock.delete()

            if jess_cant_rap.content.lower() in ('no', 'deny'):
                return await ctx.send(
                    f"> {ctx.author.mention}",
                    embed = butils.Embed(
                        description = f"Sorry {ctx.author.display_name}, seems like nobody wants to be within 3 feet of your gargantuan schlong."
                    ).set_footer(
                        text = "They denied your challenge", icon_url = ctx.author.avatar_url
                    )
                )

            chmsg = await ctx.send(
                embed = butils.Embed(
                    description = '<:FahhhS:699140533729099858> Swinging "Swords"...'
                )
            )
            await asyncio.sleep(3) # Some dramatic pausing for effect~

            author_cock = await self.get_user_cock(ctx.author)
            user_cock = await self.get_user_cock(user)

            winner = random.choices([author_cock, user_cock], weights=[author_cock.rlength, user_cock.rlength])[0]
            loser = user_cock if winner != user_cock else author_cock

            winnings = await self.swordfight_win(
                winner = winner,
                loser = loser
            )

            return await chmsg.edit(
                embed = butils.Embed(
                    description = f"{winner.user.display_name} stole `{round(winnings, 2):,}` inches off of {loser.user.display_name}'s penis! That sucks lol."
                ).set_author(
                    name = f"{winner.user.display_name} won the swordfight!"
                ).set_thumbnail(
                    url = winner.user.avatar_url
                )
            )

    @swordfight.error
    async def sf_errors(self, ctx, error):
        if isinstance(error, CommandOnCooldown):
            return await ctx.send(
                content=f"> {ctx.author.mention}",
                embed = butils.Embed(
                    description=f"Sorry but your horny ass needs to wait for {error.humanize} before you can wave your dick around again.",
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



            

    @commands.command()
    async def hug(self, ctx, user : discord.Member):
        """hug somebody"""
        async with aiohttp.ClientSession() as s:
            async with s.get('%s/img/hug' % _NEKOS_API_ENDPOINT) as resp:
                t=await resp.json()
        return await ctx.send(
            embed = butils.Embed(
                timestamp=discord.Embed.Empty
            ).set_image(
                url = t['url']
            ).set_author(
                name = f"{ctx.author} hugged {user}! 💖",
                icon_url = ctx.author.avatar_url
            )
        )
    @commands.command()
    async def kiss(self, ctx, user : discord.Member):
        """kiss a friend"""
        async with aiohttp.ClientSession() as s:
            async with s.get('%s/img/kiss' % _NEKOS_API_ENDPOINT) as resp:
                t=await resp.json()
        return await ctx.send(
            embed = butils.Embed(
                timestamp=discord.Embed.Empty
            ).set_image(
                url = t['url']
            ).set_author(
                name = f"{ctx.author} kissed {user}~! 💖",
                icon_url = ctx.author.avatar_url
            )
        )

    @commands.command(aliases=['smack'])
    async def spank(self, ctx, user : discord.Member):
        """kiss a friend"""
        async with aiohttp.ClientSession() as s:
            async with s.get('%s/img/spank' % _NEKOS_API_ENDPOINT) as resp:
                t=await resp.json()
        return await ctx.send(
            embed = butils.Embed(
                timestamp=discord.Embed.Empty
            ).set_image(
                url = t['url']
            ).set_author(
                name = f"{ctx.author} spanked {user}...",
                icon_url = ctx.author.avatar_url
            )
        )

    @commands.command()
    async def slap(self, ctx, user : discord.Member):
        """slap somebody, HARD"""
        async with aiohttp.ClientSession() as s:
            async with s.get('%s/img/slap' % _NEKOS_API_ENDPOINT) as resp:
                t=await resp.json()
        return await ctx.send(
            embed = butils.Embed(
                timestamp=discord.Embed.Empty
            ).set_image(
                url = t['url']
            ).set_author(
                name = f"{ctx.author.display_name} slapped the absolute fuck outta {user.display_name}. God damn.",
                icon_url = ctx.author.avatar_url
            )
        )
    @commands.command()
    async def cuddle(self, ctx, user : discord.Member):
        """cuddle your homies, no homo."""
        async with aiohttp.ClientSession() as s:
            async with s.get('%s/img/cuddle' % _NEKOS_API_ENDPOINT) as resp:
                t=await resp.json()
        return await ctx.send(
            embed = butils.Embed(
                timestamp=discord.Embed.Empty
            ).set_image(
                url = t['url']
            ).set_author(
                name = f"{ctx.author.display_name} cuddled {user.display_name}~* 💖",
                icon_url = ctx.author.avatar_url
            )
        )

    @commands.command()
    async def kill(self, ctx, *, user : discord.Member):
        """ Kill somebody """
        ka = random.choice(self._kill_adjectives)
        kw = random.choice(self._kill_weapons)
        if user.id in self.client.owner_ids:
            return await ctx.send(
                f"{user} cannot be killed."
            )


        return await ctx.send(
            embed = butils.Embed(
                description = f"{ctx.author.mention} {ka} {user.mention} with {kw}."
            )
        )


def setup(client):
    client.add_cog(FunCommands(client))