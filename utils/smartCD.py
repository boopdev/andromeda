#
# boop's Smart Cooldown Util
#    Acts like a regular cooldown, but will save to the database when the bot is shut off.
#

# POSTGRES QUERY:
_pgq="""CREATE TABLE IF NOT EXISTS smartcd(userid BIGINT, guildid BIGINT, channelid BIGINT, cmd TEXT, cd TIMESTAMP);"""

import enum, discord, datetime, humanize
from discord.ext import commands

class CooldownType(enum.IntEnum):
    user = 0
    member = 1
    guild = 2
    channel = 3

class CommandOnCooldown(commands.CheckFailure):
    def __init__(self, t):
        self._t = t if isinstance(t, datetime.timedelta) else datetime.timedelta(seconds=t)
        if not isinstance(t, int):
            self.time_left = t.total_seconds() if t.total_seconds() > 0 else t.total_seconds() * -1
        else:
            self.time_left = 0

    @property
    def humanize(self):
        return humanize.naturaldelta(self._t)

def __get_cd_differences(cdst, cdsec):
    return datetime.datetime.utcnow() - (cdst + datetime.timedelta(seconds=cdsec))

async def _check_cooldown(ctx, user : discord.User, cdsec : int, cmd : commands.Command, cd_type : CooldownType):
    if cd_type == 0:
        results = await ctx.bot.db.fetchrow("SELECT * FROM smartcd WHERE userid=$1 AND cmd=$2;", user.id, cmd.qualified_name)
    elif cd_type == 1:
        results = await ctx.bot.db.fetchrow("SELECT * FROM smartcd WHERE userid=$1 AND guildid=$2 AND cmd=$3;", user.id, ctx.guild.id, cmd.qualified_name)
    elif cd_type == 2:
        results = await ctx.bot.db.fetchrow("SELECT * FROM smartcd WHERE guildid=$1 AND cmd=$2;", ctx.guild.id, cmd.qualified_name)
    elif cd_type == 3:
        results = await ctx.bot.db.fetchrow("SELECT * FROM smartcd WHERE channelid=$1 AND cmd=$2;", ctx.channel.id, cmd.qualified_name)
    else: # If an invalid cd_type was given, (which is highly unlikely to ever happen)
        raise ValueError("What the fuck kinda cd_type you supplying here retard...")
        
    if results in (None, (), []):
        return True, 0 # Because the cooldown entry isnt in there, the cooldown probably doesnt exist
    elif results['cd'] + datetime.timedelta(seconds=cdsec) <= datetime.datetime.utcnow():
        return True, 0
    else:
        return False, __get_cd_differences(results['cd'], cdsec)

async def _update_cooldown(ctx, user : discord.User, cmd : commands.Command, cd_type : CooldownType):
    if cd_type == 0:
        q = await ctx.bot.db.fetchrow("SELECT * FROM smartcd WHERE userid=$1 AND cmd=$2;", user.id, cmd.qualified_name)
    elif cd_type == 1:
        q = await ctx.bot.db.fetchrow("SELECT * FROM smartcd WHERE userid=$1 AND guildid=$2 AND cmd=$3;", user.id, ctx.guild.id, cmd.qualified_name)
    elif cd_type == 2:
        q = await ctx.bot.db.fetchrow("SELECT * FROM smartcd WHERE guildid=$1 AND cmd=$2;", ctx.guild.id, cmd.qualified_name)
    elif cd_type == 3:
        q = await ctx.bot.db.fetchrow("SELECT * FROM smartcd WHERE channelid=$1 AND cmd=$2;", ctx.channel.id, cmd.qualified_name)
    else: # If an invalid cd_type was given, (which is highly unlikely to ever happen)
        raise ValueError("What the fuck kinda cd_type you supplying here retard...")

    if q in (None, (), []):
        await ctx.bot.db.execute(
            "INSERT INTO smartcd(userid, guildid, channelid, cmd, cd) VALUES ($1, $2, $3, $4, $5)",
            user.id, ctx.guild.id, ctx.channel.id, cmd.qualified_name, datetime.datetime.utcnow()    
        )
    else:
        await ctx.bot.db.execute(
            "UPDATE smartcd SET cd=$1 WHERE userid=$2 AND cmd=$3 AND cd=$4",
            datetime.datetime.utcnow(), user.id, cmd.qualified_name, q['cd']
        )
    
def smart_cooldown(cooldown_seconds : int, _type : CooldownType = CooldownType.user):
    async def predicate(ctx):
        cdschk, cdtime = await _check_cooldown(ctx, user = ctx.author, cdsec=cooldown_seconds, cmd=ctx.command, cd_type=_type)
        if cdschk:
            # Update cooldown, return true
            await _update_cooldown(
                ctx=ctx,
                user=ctx.author,
                cmd=ctx.command,
                cd_type=_type
            )
            return True
        else:
            raise CommandOnCooldown(t=cdtime)
    return commands.check(predicate)