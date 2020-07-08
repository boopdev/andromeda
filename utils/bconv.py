import discord, asyncio, string, typing
from discord.ext import commands
from utils import butils

class CogConverter(commands.Converter):
    async def convert(self, ctx, arg):
        
        # Grab cog object based on qualified name
        if arg.lower() in [c.qualified_name.lower() for c in ctx.bot.cogs.values()] or len(list(filter(lambda c: arg.lower() == c.qualified_name.lower(), ctx.bot.cogs.values()))) == 1:
            return list(filter(lambda c: arg.lower() == c.qualified_name.lower(), ctx.bot.cogs.values()))[0]
        
        # Grab cog object based on name (CogMeta)
        #elif arg.lower() in [c.name.lower() for c in ctx.bot.cogs.values()] or len(list(filter(lambda c: arg.lower() == c.name.lower(), ctx.bot.cogs.values()))) == 1:
        #    return list(filter(lambda c: arg.lower() == c.name.lower(), ctx.bot.cog.values()))[0]
        
        # Grab cog if it starts with a certain string
        elif len(list(filter(lambda c: c.qualified_name.lower().startswith(arg.lower()), ctx.bot.cogs.values()))):
            return list(filter(lambda c: c.qualified_name.lower().startswith(arg.lower()), ctx.bot.cogs.values()))[0]

        else:
            raise commands.BadArgument(message="No cog found!")

class CommandConverter(commands.Converter):
    async def convert(self, ctx, argument):
        
        # Check for name
        if len(list(filter(lambda com: com.name.lower() == argument.lower(), ctx.bot.commands))) == 1:
            return list(filter(lambda com: com.name.lower() == argument.lower(), ctx.bot.commands))[0]

        # Check aliases
        elif len(list(filter(
            lambda c: argument.lower() in [i.lower() for i in c.aliases],
            ctx.bot.commands
        ))) == 1:
            return list(filter(
                lambda c: argument.lower() in [i.lower() for i in c.aliases],
                ctx.bot.commands
            ))[0]
        
        else:
            raise commands.BadArgument(message="No command found!")

AdvancedIntegerConfig = [
    {
        "name" : "thousand",
        "extension-symbol" : "k",
        "scientific-notation-exponent" : 3
    },
    {
        "name" : "million",
        "extension-symbol" : "m",
        "scientific-notation-exponent" : 6
    },
    {
        "name" : "billion",
        "extension-symbol" : "b",
        "scientific-notation-exponent" : 9
    },
    {
        "name" : "trillion",
        "extension-symbol" : "t",
        "scientific-notation-exponent" : 12
    },
    {
        "name" : "quadrillion",
        "extension-symbol" : "q",
        "scientific-notation-exponent" : 15
    }
]

class AdvancedIntConverter(commands.Converter):
    async def convert(self, ctx, arg : typing.Union[int, str]): # We're presuming 'arg' is going to be representing some sort of integer

        # If somehow an integer is provided, then just use that idc
        if isinstance(arg, int):
            print("fuck")
            return arg

        # Checks to see if it's just a regular representation of an integer
        if all([i in string.digits + "+-" for i in str(arg)]):
            try:
                return int(arg)
            except ValueError: # If it isnt a fucking integer for whatever reason
                pass

        # Checks to see if it's a integer with comma seperators
        if all([i in string.digits + "+-"  for i in str(arg.replace(',', ''))]):
            try:
                return int(arg.replace(',', ''))
            except ValueError:
                pass

        if all([i.lower() in string.digits + "e." for i in arg]):

            # Raises error if E is found more than once
            if arg.lower().count("e") > 1:
                raise commands.BadArgument("You tried to put two exponent symbols in this argument? That won't work.")
            
            
            p = arg.lower().split("e") # Splits apart the numbers

            if len(p) != 2:
                raise commands.BadArgument("Both sides require a number on them")
                return

            if '.' in p[1]:
                raise commands.BadArgument("No.")
                return

            try:
                return int(float(p[0]) * (10**int(p[1])))
            except ValueError:
                pass
        
        if all([i.lower() in string.digits + '.' + ''.join(butils.get_digit_set([q['extension-symbol'] for q in AdvancedIntegerConfig])) for i in str(arg)]):
            look_for_endpoint = list(filter(lambda q: arg.lower().endswith(q['extension-symbol']), AdvancedIntegerConfig))
            
            if len(look_for_endpoint) == 0:
                raise commands.BadArgument("No Valid Suffix Found")
                return
            
            elif len(look_for_endpoint) > 1:
                raise commands.BadArgument("This error shouldn't happen")
                return

            else:
                endpoint = look_for_endpoint[0]
                print(endpoint)

                for i in butils.get_digit_set([q['extension-symbol'] for q in AdvancedIntegerConfig]):
                    arg = arg.replace(i, '') # Removes the suffix

                print(arg)

                try:
                    return int(float(arg) * (10**int(endpoint['scientific-notation-exponent'])))
                except ValueError:
                    pass

class HexConverter(commands.Converter):
    async def convert(self, ctx, argument):
        if not all([x in string.hexdigits.lower() for x in argument.lower()]):
            raise commands.BadArgument("Invalid characters supplied in hex argument")
        return int(argument, base=16)

class EcoOreConverter(commands.Converter):
    async def convert(self, ctx, argument):
        eco_cog = ctx.bot.get_cog('Economy')

        _ores = await eco_cog.pull_ore_cache()
        
        # Check for exact reference
        for i in _ores:
            if i.name.lower() == argument.lower():
                return i

        #Check for singular similar reference
        _check_cache = []
        for i in _ores:
            if i.name.lower().startswith(argument.lower()):
                _check_cache.append(i)
        if len(_check_cache) == 1: return _check_cache[0]
        else:
            raise commands.BadArgument("No ore could be found matching/similar to the supplied argument. Try being more specific or spelling it right lol")