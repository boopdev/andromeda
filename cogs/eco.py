import discord, asyncio, math, random, typing, datetime, yaml
from discord.ext import commands
from utils import bconv, butils, smartCD, checks
from utils import butilsImg as bImg
from data import drops

# ₱ = Points

def get_experience(level : int, exponent : float = 1.4, base : int = 200):
    return base * level ** exponent

def get_level(experience : float, exponent : float = 1.4, base : int = 200):
    return (experience / base) ** (1 / exponent)

# Andromeda Economy**
class EconomyCommands(commands.Cog, name="Economy"):
    def __init__(self, client):
        self.client = client
        self.no_rob_cache = {}

        self.load_pickaxe_data() # Loads all of the pickaxes to memory

        self.pickaxe_crafting_tree = (
            'wooden_pickaxe', # This will always be the starting pickaxe, if you wanna change the starting pick then make it the first item in this tuple
            'stone_pickaxe',
            'copper_pickaxe',
            'tin_pickaxe',
            'bronze_pickaxe',
            'iron_pickaxe'
        )

    @property
    def ores(self):
        return self.__getattribute__('ore_cache')['ores']


    async def point_drop(self, channel : discord.TextChannel):
        drop_this = random.choice(
            [drops.type_drop,]
        )
        x = drop_this(channel)
        
        _m = await channel.send(
            embed = butils.Embed(
                description = x.embed_desc,
                title = x.type_this if not x.hide_answer else discord.Embed.Empty
            ).set_image(
                url = x.embed_image
            )
        )

        try:
            m = await self.client.wait_for('message', timeout=60, check = x.solves)
        except asyncio.TimeoutError:
            return await _m.edit(
                embed = butils.Embed(
                    description = "Nobody grabbed the points drop!"
                ).set_footer(
                    text = f"You all missed out on {x.reward:,}₱!",
                    icon_url = self.client.user.avatar_url
                )
            )
        else:
            winner = m.author
            
            await self.edit_balance(m.author, x.reward, append=True, bank=False, negative=False)
            await _m.delete()
            return await channel.send(
                embed = butils.Embed(
                    title = f"{m.author.display_name} got it!",
                    description = "Enjoy **{x.reward:,}₱** as a reward!"
                ).set_thumbnail(
                    url = m.author.avatar_url
                )
            )
    
    class EconomyUserData():
        def __init__(self, _raw):
            self._raw = _raw

            self.cash = _raw['cash']
            self.bank = _raw['bank']

            self.robbable = _raw['robbable']

        @property
        def net(self):
            return self._raw['cash'] + self._raw['bank']

    async def register(self, user : discord.User):
        q = await self.client.db.execute("INSERT INTO eco(userid, cash, bank) VALUES ($1, 0, 100)", user.id)
        return self.EconomyUserData(
            {
                "cash" : 0,
                "bank" : 100,
                "robbable" : False
            }
        )

    async def get_balance(self, user : discord.User):
        q=await self.client.db.fetchrow("SELECT cash, bank, robbable FROM eco WHERE userid=$1", user.id)
        if q is None:
            return await self.register(user)
        else:
            return self.EconomyUserData(q)

    async def edit_balance(self, user : discord.User, amount : int, append:bool=True, bank:bool=False, negative:bool=False):
        q = await self.get_balance(user) # Grabs user balance
        if negative: amount *= -1
        if append:
            amount += q.cash if not bank else q.bank
        if bank:
            await self.client.db.execute("UPDATE eco SET bank=$1 WHERE userid=$2", amount, user.id)
            q.bank = amount
        else:
            await self.client.db.execute("UPDATE eco SET cash=$1 WHERE userid=$2", amount, user.id)
            q.cash = amount
        return q

    async def exchange_balance(self, user : discord.User, amount : int, to_cash:bool=False):
        if to_cash:
            await self.client.db.execute("UPDATE eco SET cash=cash+$1, bank=bank-$1 WHERE userid=$2", amount, user.id)
        else:
            await self.client.db.execute("UPDATE eco SET cash=cash-$1, bank=bank+$1 WHERE userid=$2", amount, user.id)
        return await self.get_balance(user)

        

    @commands.command(aliases=['bal', 'wallet', 'points'])
    async def balance(self, ctx, *, user : discord.Member = None):
        """Displays the amount of points a member has, if not member is supplied it defaults to the author"""
        if user is None: user = ctx.author
        if user.bot: return await ctx.send("> ❌ | `Bots cannot have money.`")
        _ubal = await self.get_balance(user)
        return await ctx.send(
            embed = butils.Embed(
                description = f"**Networth** : `{_ubal.net:,} ₱`"
            ).add_field(
                name = "Cash", value=f"```\n{_ubal.cash:,} ₱```", inline=False
            ).add_field(
                name = "Bank", value=f"```\n{_ubal.bank:,} ₱```", inline=False
            ).set_author(
                name = f"{user.display_name}'s Balance", icon_url = user.avatar_url
            )
        )

    @commands.group(invoke_without_command=True)
    async def pay(self, ctx, user : discord.Member, amount : typing.Union[bconv.AdvancedIntConverter, int]):
        """Give somebody monar"""
        if user.bot: return await ctx.send("> ❌ | `You cannot pay bots.`")
        if amount <= 0:
            return await ctx.send(
                embed = butils.Embed().set_author(
                    name = "You need to pay more than 1 point.", icon_url = ctx.author.avatar_url
                )
            )
        _ubal = await self.get_balance(ctx.author)
        if _ubal.cash < amount:
            return await ctx.send(
                embed = butils.Embed().set_author(
                    name = "You don't have enough points on you to pay that much", icon_url = ctx.author.avatar_url
                ).set_footer(
                    text = "Maybe stop being so broke lol" if _ubal.net < amount else "You have enough in your bank! use .withdraw",
                    icon_url = ctx.author.avatar_url
                )
            )
        _recv = await self.get_balance(user)
        await self.edit_balance(user, amount, append=True, bank=False, negative=False)
        await self.edit_balance(ctx.author, amount, append=True, bank=False, negative=True)
        return await ctx.message.add_reaction("✅")

    @pay.command(name="all")
    async def pay_all(self, ctx, user : discord.Member):
        _cmd = self.client.get_command('pay')
        _acc = await self.get_balance(user)
        await ctx.invoke(_cmd, amount=_acc.cash)

    @pay.command(name="half")
    async def pay_half(self, ctx, user : discord.Member):
        _cmd = self.client.get_command('pay')
        _acc = await self.get_balance(user)
        await ctx.invoke(_cmd, amount=math.floor(_acc.cash/2))

    #@commands.cooldown(1, 180, commands.BucketType.user)
    @commands.guild_only()
    @commands.command()
    async def rob(self, ctx, user : discord.Member):
        """Rob somebody monar"""

        if user.id in self.no_rob_cache:
            if (datetime.datetime.utcfromtimestamp(self.no_rob_cache[user.id]) + datetime.timedelta(minutes=10)).timestamp() <= datetime.datetime.utcnow().timestamp():
                return await ctx.send(
                    embed = butils.Embed(
                        description=f"{user.mention} can't be robbed on account of them being robbed recently."
                    ).set_author(
                        name = f"{user.display_name} is still recouping their loses!",
                        icon_url = user.avatar_url
                    ).set_footer(
                        text = "You'll be able to rob them after 10 minutes has passed.",
                        icon_url = ctx.bot.user.avatar_url
                    )
                )
            else:
                del self.no_rob_cache[user.id] # Clears their name from robbery cache
        
        _uac = await self.get_balance(user)
        if _uac.cash == 0:
            return await ctx.send(
                f"> {ctx.author.mention}\n> ❌ | `{user.display_name} has nothing on them you can rob retard!`"
            )

        max_robbable_amount, min_robbable_amount = round(_uac.net * 0.5), round(_uac.net * 0.2)
        robbed = random.choice([True, False])
        if robbed:
            rob_amount = random.randint(
                min_robbable_amount,
                max_robbable_amount
            )

            if rob_amount > _uac.cash:
                rob_amount = _uac.cash

            await self.edit_balance(user, rob_amount, negative=True, bank=False, append=True)
            await self.edit_balance(ctx.author, rob_amount, negative=False, bank=False, append=True)

            self.no_rob_cache[user.id] = datetime.datetime.utcnow().timestamp()

            return await ctx.send(
                embed = butils.Embed(
                    description = f"{ctx.author.mention} got away with `{rob_amount:,} ₱`",
                    colour = self.client._colours['monar']
                ).set_author(
                    name = f"{user.display_name.upper()} WAS ROBBED!", icon_url = ctx.author.avatar_url
                )
            )
        
        return await ctx.send(
            f"> ❌ | {ctx.author.mention} failed to rob **{user.display_name}**"
        )

    @commands.group(invoke_without_command=True, aliases=['with'])
    async def withdraw(self, ctx, amount : typing.Union[bconv.AdvancedIntConverter, int]):
        """Take monar from bank"""
        if amount <= 0:
            return await ctx.send(f"> ❌ | {ctx.author.mention} you need to withdraw at least one point dumbass.")

        _uac = await self.get_balance(ctx.author)

        if _uac.bank < amount:
            return await ctx.send(
                f"> ❌ | {ctx.author.mention}",
                embed = butils.Embed(
                    colour=self.client._colours['no'],
                    description="You don't have that much money in your account!"
                ).set_author(
                    name = "Sorry broke bitch...", icon_url = ctx.author.avatar_url
                )
            )

        await self.exchange_balance(ctx.author, amount=amount, to_cash=True)
        return await ctx.message.add_reaction("✅")
    
    @withdraw.command(name="half")
    async def withdraw_half(self, ctx):
        _cmd = self.client.get_command('withdraw')
        _acc = await self.get_balance(ctx.author)
        await ctx.invoke(_cmd, amount=math.floor(_acc.bank/2))

    @withdraw.command(name="all")
    async def withdraw_all(self, ctx):
        _cmd = self.client.get_command('withdraw')
        _acc = await self.get_balance(ctx.author)
        await ctx.invoke(_cmd, amount=_acc.bank)

    @commands.group(invoke_without_command=True, aliases=['dep'])
    async def deposit(self, ctx, amount : typing.Union[bconv.AdvancedIntConverter, int]):
        """put monar in da bank"""
        if amount <= 0:
            return await ctx.send(f"> ❌ | {ctx.author.mention} you need to deposit at least one point dumbass.")

        _uac = await self.get_balance(ctx.author)

        if _uac.cash < amount:
            return await ctx.send(
                f"> ❌ | {ctx.author.mention}",
                embed = butils.Embed(
                    colour=self.client._colours['no'],
                    description="You don't have that much money on you fucknuts!"
                ).set_author(
                    name = "Sorry broke bitch...", icon_url = ctx.author.avatar_url
                )
            )

        await self.exchange_balance(ctx.author, amount=amount, to_cash=False)
        return await ctx.message.add_reaction("✅")
    
    @deposit.command(name="all")
    async def deposit_all(self, ctx):
        _cmd = self.client.get_command('deposit')
        _acc = await self.get_balance(ctx.author)
        await ctx.invoke(_cmd, amount=_acc.cash)

    @deposit.command(name="half")
    async def deposit_half(self, ctx):
        _cmd = self.client.get_command('deposit')
        _acc = await self.get_balance(ctx.author)
        await ctx.invoke(_cmd, amount=math.floor(_acc.cash/2))

    #
    # Mining Shit
    # Brrrr Minecraft Mode
    #

    async def get_mining_account(self, user : discord.User):
        qr=await self.client.db.fetchrow("SELECT * FROM mining WHERE userid=$1", user.id)
        if qr is not None:
            return self.ecoMiningUser(
                client=self.client,
                **{i[0] : i[1] for i in qr.items()} #voila i am magician
            )
        else:
            return await self.register_mining_account(user=user)

    async def register_mining_account(self, user : discord.Member):
        _data = {
            'userid' : user.id,
            'pickaxe' : self.pickaxe_crafting_tree[0],
            'experience' : 0,
            'levelnotif' : 1, # 1 above the current level
            'oresmined' : 0
        }
        await self.client.db.execute(
            "INSERT INTO mining(userid, pickaxe, experience, levelnotif, oresmined) VALUES ($1, $2, 0, 1, 0)",
            _data['userid'], _data['pickaxe']    
        )
        return self.ecoMiningUser(client=self.client, **_data)

    class ecoMiningUser():
        def __init__(self, *args, **kwargs):
            self._client = kwargs.get('client', None)

            self.id = kwargs.get('userid', -1)
            self.pickaxe_id = kwargs.get('pickaxe', 'wooden_pickaxe')
            self.experience = kwargs.get('experience', 0)
            self.levelnotif = kwargs.get('levelnotif', 1)
            self.oresmined = kwargs.get('oresmined', 0)

        @property
        def level_up(self):
            return get_level(self.experience) >= self.levelnotif

        @property
        def levelup_progress(self):
            _l = get_experience(self.current_level)
            return ((self.experience - _l) / (get_experience(level=self.levelnotif) - _l)) * 100

        @property
        def pickaxe(self):
            return self._client.get_cog("Economy").get_pickaxe(self.pickaxe_id)

        @property
        def current_level(self):
            return math.floor(get_level(self.experience))

        async def get_user_ores(self):
            o = await self._client.db.fetch("SELECT oreid, amount FROM ores WHERE userid=$1 AND amount>0", self.id)
            if o in ((), [], None): return {}
            else:
                x=[]
                for i in o:
                    u = await self._client.get_cog("Economy").get_ore(i['oreid'])
                    x.append((u, i['amount']))
                return x

    class ecoMiningPickaxe(yaml.YAMLObject):
        yaml_tag=u'!Pickaxe'
        def __init__(self, *args, **kwargs):
            self.client = None

            self.id = kwargs.get('id', 'broken_pickaxe')
            self.name = kwargs.get('name', 'Broken Pickaxe')
            self.level = kwargs.get('level', -1)
            self.multiplier = kwargs.get('multiplier', 1)
            self.ores = kwargs.get('ores', list())
            self.crafting = kwargs.get('crafting', d=dict()) # Empty dict for no crafting recipe

        def __repr__(self):
            return f"<PickaxeObj id={self.id} name={self.name}>"

        @property
        def next_pickaxe(self):
            if not self.id in self.client.get_cog("Economy").pickaxe_crafting_tree:
                return None

            if self.id == self.client.get_cog("Economy").pickaxe_crafting_tree[len(self.client.get_cog("Economy").pickaxe_crafting_tree)-1]: # If this pickaxe is the last one
                return None

            return self.client.get_cog("Economy").get_pickaxe(
                    self.client.get_cog("Economy").pickaxe_crafting_tree[
                        self.client.get_cog("Economy").pickaxe_crafting_tree.index(self.id)+1
                    ]
            )

        async def get_ores(self):
            _c=self.client.get_cog("Economy")
            x=[]
            for i in self.ores:
                u=await _c.get_ore(i)
                x.append(u)
            return x

    class ecoMiningOre():
        def __init__(self, *args, **kwargs):
            self.oreid = kwargs.get('oreid', -1)
            self.name = kwargs.get('name', 'brokey ore')
            self._value = kwargs.get('value', 0)
            self._rarity = kwargs.get('rarity', 0)

        def __eq__(self, value):
            if not isinstance(value, self.__class__):
                return ValueError("only other ores may be passed to the __eq__ dunder func")
            return value.oreid == self.oreid or value.name == self.name

        def __repr__(self):
            return f"<Ore={self.oreid} name='{self.name}'>"

        @property
        def base_experience(self):
            bxp = round((self.oreid * ((self._value / (self.oreid + self._rarity)) / self._rarity)+1.5))
            return bxp if bxp >= 1 else 1

        @property
        def rarity(self):
            return round(self._rarity * 1.5)

        @property
        def value(self): return round(self._value * 2)

    def get_pickaxe(self, pickaxe_id):
        p= list(filter(lambda x: x.id == pickaxe_id, self.pickaxes))
        if len(p)>=1: return p[0]
        else: return None

    def load_pickaxe_data(self):
        with open('./data/pickaxes.yml', 'r') as f:
            data = yaml.load_all(
                f
            )
            data = [o for o in data]
        for i in data:
            i.__setattr__('client', self.client)
        self.__setattr__('pickaxes', data)

    async def get_all_ores(self):
        q=await self.client.db.fetch("SELECT * FROM ore_definitions")
        return [self.ecoMiningOre(**y) for y in q]

    async def update_ore_cache(self):
        if not hasattr(self, 'ore_cache'):
            _o=await self.get_all_ores()
            self.__setattr__('ore_cache', {'ores' : _o, "t" : datetime.datetime.utcnow()})
            self.client.logger.info("Initial Ore Cache Update Completed")
        elif hasattr(self, 'ore_cache') and datetime.datetime.utcnow() - self.__getattribute__('ore_cache')['t'] > datetime.timedelta(seconds=5):
            _o=await self.get_all_ores()
            self.__setattr__('ore_cache', {'ores' : _o, "t" : datetime.datetime.utcnow()})
            self.client.logger.info(">5m Ore Cache Update Completed")
        else:
            return

    async def get_ore(self, ore):
        await self.update_ore_cache()

        if not isinstance(ore, self.ecoMiningOre):
            # Creates an ecoMiningOre object for the __eq__ thingy
            ore = self.ecoMiningOre(name=ore, oreid=ore)

        c=list(filter(lambda o: o == ore, self.ores))
        return c[0]

    # This is the same thing as self.get_all_ores, but updates the cache and pulls from that instead
    async def pull_ore_cache(self):
        await self.update_ore_cache()
        return self.ore_cache['ores']

    async def mine_ore(self, user : discord.User, ore : ecoMiningOre, amount : int):
        _mc_acc = await self.get_mining_account(user)
        exp_earned = round(((ore.base_experience * amount)) * math.floor(1 + round(divmod(_mc_acc.current_level, 2)[0])/2))
        await self.client.db.execute("UPDATE mining SET oresmined=oresmined+$1, experience=experience+$3 WHERE userid=$2", amount, user.id, exp_earned)
        q=await self.client.db.fetchrow("SELECT * FROM ores WHERE userid=$1 AND oreid=$2", user.id, ore.oreid)
        if q is None:
            await self.client.db.execute("INSERT INTO ores VALUES ($1, $2, $3);", user.id, ore.oreid, amount)
        else:
            await self.client.db.execute("UPDATE ores SET amount=amount+$1 WHERE oreid=$2 AND userid=$3", amount, ore.oreid, user.id)
        return exp_earned


    @commands.group(invoke_without_command=True)
    async def mining(self, ctx, user : discord.Member = None):
        """Shows a user's mining profile"""
        if user is None: user = ctx.author
        _mc = await self.get_mining_account(user)
        f=await bImg.make_progress_bar(self.client, round(_mc.levelup_progress))

        return await ctx.send(
            embed = butils.Embed(
                description=f"\⛏️ **Pickaxe:** `{_mc.pickaxe.name}`\n\💎 **Ores Mined:** `{_mc.oresmined:,}`\n\💪 **Level:** `{_mc.current_level:,}`\n\⌛ **Total Experience:** `{round(_mc.experience):,}`"
            ).set_image(
                url='attachment://progressbar.jpeg'
            ).set_author(
                name = f"{user.display_name}'s Mining Statistics", icon_url = user.avatar_url
            ).set_footer(
                icon_url = self.client.scarlyst.icon_url,
                text = f"{round(_mc.experience-(get_experience(_mc.current_level)))}/{round(get_experience(_mc.current_level+1)-(get_experience(_mc.current_level)))} ({round(_mc.levelup_progress,2)}%)"
            ),
            file = f
        )

    @mining.command(name="ores", aliases=['bag', 'ore', 'rocks', 'minerals', 'satchel', 'sack'])
    async def mining_ores(self, ctx):
        """Shows a user's mining bag, contains all of your ores"""
        _mc = await self.get_mining_account(ctx.author)
        _mc_ores = await _mc.get_user_ores()

        _mc_ores = sorted(_mc_ores, key=lambda i: i[1], reverse=True)

        await ctx.send(
            embed = butils.Embed(
                description = "\n".join(
                    [f"**{o.name.title()} Ore** > `{a:,}`" for o,a in _mc_ores]
                )
            ).set_author(
                icon_url = ctx.author.avatar_url,
                name = f"{ctx.author.display_name}'s Ore Bag"
            )
        )

    @mining.command(name="upgrade")
    async def mining_upgrade(self, ctx):
        """Upgrade your pickaxe"""
        _mc = await self.get_mining_account(ctx.author)
        _pickaxe = _mc.pickaxe.next_pickaxe

        if _pickaxe is None:
            return await ctx.send(
                content=f"> {ctx.author.mention}",
                embed = butils.Embed(
                    colour = self.client._colours['monar'],
                    description = "<:pogS:684134572950421639> **You have the highest tier pickaxe, good work king.**"
                ).set_author(
                    name = f"{ctx.author.display_name}", icon_url = ctx.author.avatar_url
                )
            )

        _ores = await _mc.get_user_ores()
        _formatted_ores = {k.name : v for k, v in _ores}
        
        reqs = {
            f"Level {_pickaxe.level}" : _mc.current_level >= _pickaxe.level,
        }

        # Add ore ingredient requirements
        for i, a in _pickaxe.crafting.items():
            reqs[f"{a:,} " + i.title()] = _formatted_ores.get(i) >= a

        m = await ctx.send(
            embed = butils.Embed(
                description = "Upgrading your pickaxe will give you the ability to mine more ores as well as more valuable ores! You'll be notified when you are able to upgrade to the next pickaxe when you mine and reach the respective level for that pickaxe.",
                title = "Wanna upgrade your pickaxe?"            
            ).add_field(
                name = f"Ingredients ❱ {_pickaxe.name}",
                value = butils.checklist_diff(
                    reqs
                )
            ).set_author(
                name = f"{ctx.author.display_name}", icon_url = ctx.author.avatar_url
            )
        )

        # Add a block for if people try to upgrade when they are underleveled
        if not _mc.current_level >= _pickaxe.level:
            return

        if all([_formatted_ores.get(k) >= v for k, v in _pickaxe.crafting.items()]):
            await m.edit(embed=m.embeds[0].set_footer(text="React with 🔨 to upgrade your pickaxe!"))
            await m.add_reaction(
                "🔨"
            )
            try:
                r, u = await self.client.wait_for("reaction_add", check=lambda r,u: u == ctx.author and str(r.emoji) == '🔨' and r.message.id == m.id, timeout=30)
            except asyncio.TimeoutError:
                return await m.remove_reaction("🔨")
            else:
                print("coom")
                b = {}
                for o, a in _pickaxe.crafting.items():
                    b[o] = await self.get_ore(o)
                await self.client.db.executemany(
                    "UPDATE ores SET amount=amount-$1 WHERE userid=$2 AND oreid=$3",
                    [
                        [v, ctx.author.id, b[k].oreid] for k, v in _pickaxe.crafting.items()
                    ]
                )
                await self.client.db.execute("UPDATE mining SET pickaxe=$1 WHERE userid=$2", _pickaxe.id, ctx.author.id)
                return await m.edit(
                    embed = discord.Embed(
                        colour = self.client._colours['yes'],
                        title = "Congratulations!",
                        description = "You upgraded your pickaxe!"
                    ).set_author(
                        name = f"{ctx.author.display_name}", icon_url = ctx.author.avatar_url
                    )
                )
        

    #@checks.require_rank("developer")
    @commands.group(aliases=['sellores'], invoke_without_command=True)
    async def sellore(self, ctx, ore : bconv.EcoOreConverter, amount : int = None):
        _mc = await self.get_mining_account(ctx.author)
        _mc_ores = await _mc.get_user_ores()
        
        _ore_count = 0
        for o, c in _mc_ores:
            if o == ore:
                _ore_count = c
                break
        if _ore_count == 0: return await ctx.send(
            embed = butils.Embed(
                description = f"Sorry {ctx.author.mention}, You don't seem to have any {ore.name.title()} Ore!",
                colour = self.client._colours['no']
            ).set_author(
                name = f"{ctx.author}", icon_url=ctx.author.avatar_url
            )
        )

        if amount is not None and _ore_count < amount:
            return await ctx.send(
                embed = butils.Embed(
                    description = f"Sorry {ctx.author.mention}, You only have {_ore_count:,} {ore.name.title()} Ore!",
                    colour = self.client._colours['no']
                ).set_author(
                    name = f"{ctx.author}", icon_url=ctx.author.avatar_url
                )
            )
        if amount is not None and amount < _ore_count: _ore_count = amount # Add the restriction

        sold_for = _ore_count * ore.value # We finna do this in case later theres new price declaration shit

        await self.client.db.execute(
            "UPDATE ores SET amount=amount-$1 WHERE userid=$2 AND oreid=$3",
            _ore_count, ctx.author.id, ore.oreid
        )

        await self.edit_balance(
            ctx.author, sold_for, append=True, bank=False, negative=False
        )

        return await ctx.send(
            embed = butils.Embed(
                description=f"You sold **{_ore_count:,} {ore.name.title()}** {'Ore' if ore.name != 'stone' else ''} for **{sold_for:,}₱**",
                colour = self.client._colours['monar']
            ).set_author(
                name = str(ctx.author), icon_url=ctx.author.avatar_url
            )
        )

    @sellore.command(name='all')
    async def sellore_all(self, ctx):
        """Sells all of your ores."""
        _mc = await self.get_mining_account(ctx.author)
        _mc_ores = await _mc.get_user_ores()

        if _mc_ores == {}:
            return await ctx.send(
                content=f"> {ctx.author.mention}",
                embed = butils.Embed(
                    colour = self.client._colours['no'],
                    description="You have no ores in your mining bag!"
                ).set_author(
                    name = f"{ctx.author}", icon_url=ctx.author.avatar_url
                )
            )

        await self.client.db.execute("DELETE FROM ores WHERE userid=$1", ctx.author.id)

        monar = sum(
            [o.value * a for o, a in _mc_ores]
        )

        await self.edit_balance(
            ctx.author, monar, append=True, bank=False, negative=False
        )

        return await ctx.send(
            embed = butils.Embed(
                colour = self.client._colours['monar'],
                description = f"You sold {sum([i[1] for i in _mc_ores])} ores for {monar:,}₱"
            ).set_author(
                name = str(ctx.author), icon_url=ctx.author.avatar_url
            )
        )


    #@checks.require_rank('developer')
    @smartCD.smart_cooldown(300) # 300 seconds, 5 minutes
    @commands.command()
    async def mine(self, ctx):
        """Grab a pickaxe and mine some shit you broke ass bitch"""
        _mp = await self.get_mining_account(ctx.author)
        _mp_ores = await _mp.pickaxe.get_ores()

        ore = random.choice(_mp_ores)
        
        ore_count = round(random.uniform(
            1 * ore.rarity * _mp.pickaxe.multiplier,
            3 * ore.rarity * _mp.pickaxe.multiplier
        ))
        
        if ore_count < 1: ore_count = 1 # At least one ore should always be mined
        _e=await self.mine_ore(ctx.author, ore, ore_count)

        _lum="" # Set default user level up text to none, might be replaced later...
            # User levelled up
        if _mp.experience + _e >= get_experience(_mp.current_level+1) or _mp.experience + _e >= get_experience(_mp.levelnotif):
            
            level = math.floor(get_level(_mp.experience + _e))
            await self.client.db.execute("UPDATE mining SET levelnotif=$2 WHERE userid=$1", ctx.author.id, level+1)
            _lum += f"<:pogS:684134572950421639> Congrats! You're now level `{level:,}` <:pogS:684134572950421639>"

            if _mp.pickaxe.next_pickaxe is not None:
                if _mp.pickaxe.next_pickaxe.level == level:
                    _lum+=str("\n" + f"<a:kittyS:571052714776330240> **You can now craft a {_mp.pickaxe.next_pickaxe.name}!**")

        _mp = await self.get_mining_account(ctx.author) # refresh data?
        f = await bImg.make_progress_bar(self.client, round(_mp.levelup_progress))

        return await ctx.send(
            embed = butils.Embed(
                description = f"You went mining and found **{ore_count} {ore.name.title()} ore!**\n> You earned `{_e:,} exp`!\n\n{_lum}",
                colour = self.client._colours['default']
            ).set_author(
                icon_url = ctx.author.avatar_url, name=f"{ctx.author.display_name} went mining..."
            ).set_image(
                url = "attachment://progressbar.jpeg"
            ).set_footer(
                text=f"{round(get_experience(_mp.current_level+1) - _mp.experience)} more experience to level {_mp.current_level+1}!",
                icon_url = self.client.scarlyst.icon_url
            ),
            file=f
        )

    @mine.error
    async def mine_error(self, ctx, err):
        if isinstance(err, smartCD.CommandOnCooldown):
            return await ctx.send(
                embed = self.client.get_cog("Errors")._unified_error_format(
                    ctx,
                    f"You have to wait {err.humanize} before you can go mining again",
                    show_help=False, title=None
                )
            )
        else:
            await self.client.db.execute(
                "DELETE FROM smartcd WHERE userid=$1 AND cmd=$2",
                ctx.author.id, ctx.command.qualified_name
            )
            return await self.client.get_cog("Errors")._handle_errors(ctx, err)

    @commands.command()
    async def ecotest(self, ctx, i : int):
        f = await bImg.make_progress_bar(self.client, progress=i, color=self.client._colours['monar'])
        await ctx.send(
            embed = butils.Embed(colour=self.client._colours['monar']).set_image(
                url = 'attachment://progressbar.jpeg'
            ),
            file=f
        )

def setup(client):
    client.add_cog(EconomyCommands(client=client))