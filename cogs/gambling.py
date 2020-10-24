import discord, asyncio, random, math
from discord.ext import commands
from utils import bconv, butils

class GamblingCog(commands.Cog, name="Gambling"):
    def __init__(self, client):
        self.client = client

        self.eco = self.client.get_cog("Economy")

        self.max_bet = 1000
        # Basically bet * (win)
        self.slot1wins = {
            "🕸️" : 0.5,
            "🦂" : 0.75,
            "🦇" : 1,
            "🕷️" : 1.5,
            "🍬" : 2,
            "🎃" : 3,
            "🍭" : 5

        }

    async def verify_bet(self, user : discord.User, bet : int):
        bal = await self.eco.get_balance(user)
        return bal.cash >= bet, bet - bal.cash

    @commands.command()
    async def slots(self, ctx, bet : int):
        """Classic 1 line slots"""
        v, a = await self.verify_bet(ctx.author, bet)

        if not v:
            return await ctx.send(
                f"> You need **{a}** more to bet that much!"
            )

        if bet > self.max_bet:
            return await ctx.send(
                f"> Max bet is set to `{self.max_bet:,}`"
            )

        w = random.choices(
            population=[None] + list(self.slot1wins.keys()),
            weights=[math.ceil(len(self.slot1wins) * 1.55)] + [-3 * math.log(i) + 10 for i, x in enumerate(self.slot1wins, start=1)],
            k = 1
        )
        w=w[0] # Pop the item from da list

        if w is not None:
            bw = round(bet * self.slot1wins[w])
        else:
            bw = 0
            
        nb = await self.eco.edit_balance(user = ctx.author, amount = bw - bet, append = True, bank = False)

        if bw > 0:
            x = f"{w}" * 3
        else:
            x = [random.choice(list(self.slot1wins.keys())) for i in range(3)]
            if len(set(x)) == 1:
                x = x[:2] + random.choice([i for i in list(self.slot1wins.keys()) if i != x[:1]])
            x = ''.join(x)
        
        return await ctx.send(
            embed = butils.Embed(
                colour = self.client._colours['yes'] if bw > 0 else self.client._colours['no'],
                description = f"You won `{bw:,}` points\n*You now have {nb.cash} points*"
            ).set_author(
                name = f"{ctx.author} bet {bet:,} points...", icon_url= ctx.author.avatar_url
            ).add_field(
                name = f"[ + {bw:,} ]", value = f"{x}"
            )
        )




def setup(client):
    client.add_cog(GamblingCog(client))