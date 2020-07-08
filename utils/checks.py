import discord, asyncio
from discord.ext import commands

class MissingRequiredRank(commands.CheckFailure):
    def __init__(self, rank_title):
        self.rank_title = rank_title

    @property
    def message(self):
        return "You must be a %s to use this command!" % self.rank_title.title()

def util_get_staff_roles(client, user : discord.Member):
    _ids = [i.id for i in user.roles]
    return [i for i in client.modranks if i.id in _ids]

def require_rank(rank_title):
    async def predicate(ctx, *args, **kwargs):
        for role in ctx.bot.modranks:
            if '*' in role.inherit_tags:
                if ctx.bot.scarlyst.get_role(role.id) in ctx.author.roles:
                    return True
        mr = ctx.bot.get_modrank(rank_title)
        if mr is not None:
            t = ctx.bot.scarlyst.get_role(mr.id) in ctx.author.roles or any([mr.name in r.inherit_tags for r in util_get_staff_roles(ctx.bot, ctx.author)])
            if t: return True
            else: raise MissingRequiredRank(rank_title)
        if kwargs.get('noerror', False) == False or 'noerror' not in kwargs:
            raise MissingRequiredRank(rank_title) # RETURN ERROR
        else:
            return False # DONT RETURN ERROR
    return commands.check(predicate)
            