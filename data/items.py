import enum, math

import discord
from discord.ext import commands

class InsufficientFunds(commands.CheckFailure):
    pass

class Item():
    item_id = "_"
    name = "Item"
    shop_value = math.inf # infinite monar, so it cannot be bought i hope

    # Makes sure that the user has enough currency to purchase the item
    async def check_for_price(self, ctx):
        _ac = await ctx.bot.get_cog("Economy").get_account(ctx.author)
        return _ac.cash >= shop_value


class RoleItem(Item):
    def __init__(self, *args, **kwargs):
        self.role_id = kwargs.get('roleid', 0)

        # Make sure that it is a role id
        if isinstance(self.role_id, discord.Role):
            self.role_id = self.role_id.id

    async def on_purchase(self, ctx, *, pricecheck:bool=True):
        _g = ctx.bot.scarlyst
        _r = _g.get_role(self.role_id)
        if not await super().check_for_price(ctx): raise InsufficientFunds
        return await ctx.author.add_role(_r)
        