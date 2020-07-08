import json, discord, asyncio, sys, datetime, re, random, math, string, typing, yaml, copy
from discord.ext import commands

with open('./data/colours.yml', 'r') as f:
    _colours = yaml.load(f)

class Embed(discord.Embed):
    def __init__(self, **kwargs):

        predefined_kwargs = dict(
            colour = _colours['default'],
            #timestamp = datetime.datetime.utcnow()
        )

        for k in predefined_kwargs.keys():
            if k not in kwargs: kwargs[k] = predefined_kwargs[k] # assigns the default value
            
        super().__init__(
            **kwargs
        )

def get_owo(text):
    faces = ["owo", "UwU", ">w<", "^w^"]
    v = text
    r = re.sub('[rl]', "w", v)
    r = re.sub('[RL]', "W", r)
    r = re.sub('ove', 'uv', r)
    r = re.sub('n', 'ny', r)
    r = re.sub('N', 'NY', r)
    r = re.sub('[!]', " " + random.choice(faces) + " ", r)
    return r

def get_enchanted(text):
    english = "abcdefghijklmnopqrstuvwxyz"
    sga = "ᔑʖᓵ↸ᒷ⎓⊣⍑╎⋮ꖌꖎᒲリ𝙹!¡ᑑ∷ᓭℸ ̣ ⚍⍊∴ ̇/||⨅"
    translate_dict = {i : sga[b] for b, i in enumerate(english)}
    text = text.lower()
    for i in translate_dict.keys():
        text = text.replace(i, translate_dict[i])
    return text

def progress_bar(progress : float, _max : float, max_columns : int = 30, col_char : str = "█", col_empty : str = " "):
    filled = math.floor((progress / _max) * max_columns)
    return (col_char * filled) + (col_empty * (max_columns - filled))

from string import Template

class DeltaTemplate(Template):
    delimiter = "%"

def strfdelta(tdelta, fmt):
    d = {}
    l = {'D': 86400, 'H': 3600, 'M': 60, 'S': 1}
    rem = int(tdelta.total_seconds())

    for k in ( 'D', 'H', 'M', 'S' ):
        if "%{}".format(k) in fmt:
            d[k], rem = divmod(rem, l[k])

    t = DeltaTemplate(fmt)
    return t.substitute(**d)

# Checks if a string is an integer or if it is a hexidecimal
def is_int(arg):
    if not all(str(char) in string.digits for char in arg.split()):
        return False

    # Handles Hexidecimal
    try:
        int(arg, base=16)
    except:
        return False
    else:
        pass

    return True

# Formats all of the hexidecimals in a tuple into ints, and it they aren't hex, then keeps them integers
def format_ints(l : list):
    q = []
    for i in l:
        if "x" in l:
            q.append(int(i, base=16))
        else:
            q.append(int(i, base=10))
    if len(q) > 1:
        return q
    else:
        return q[0]

def get_digit_set(it : list):
    x = []
    for i in it:
        for part in i:
            x.append(part)
    return x

def is_greatest(item : int, _list, sortreverse:bool=True):
    if item not in _list: raise ValueError
    x = list(sorted(_list))
    if sortreverse: x = x[::-1]
    return item == x[0] 

class CogNotLoaded(commands.CheckFailure):
    pass

def cog_is_loaded(cf):
    async def predicate(ctx):
        q=cf
        if not isinstance(q, commands.Cog):
            q = ctx.bot.get_cog(q)
            if q is None: raise CogNotLoaded()
        else:
            if not q in ctx.bot.cogs: raise CogNotLoaded
        return True
    return commands.check(predicate)

def hexchar(i : float):
    return str(hex(math.floor(i)))[2:]

def rgb_to_hex(rgb):
    if len(rgb)!=3: raise ValueError("Invalid amount of arguments supplied to rgb_to_hex. Must be 3")
    p = ""
    for i in rgb: p += hexchar(i/16) + hexchar(((i/16)-math.floor(i/16))*16)
    return int(p, base=16)

def hex_to_rgb(_hex : int):
    _hex = str(hex(_hex))[2:]
    prts = [_hex[2*e:2*(e+1)] for e in range(3)]
    return (int(x, base=16) for x in prts)

def most_common(l : list):
    x = {i : l.count(i) for i in set(l)}
    return list(sorted(x, key=lambda y: x[y], reverse=True))[0]

def occurence_percentage(l):
    v={x : (l.count(x)/len(l))*100 for x in set(l)}
    return sorted(v, key=lambda x: x[1], reverse=True)

def intensify_colour(colour : int, intensity : int, *, _max : int = 100, exceed:bool=False):
    if intensity > _max and not exceed: intensity = _max
    _rgb = hex_to_rgb(colour)
    _new_rgb = []
    for c in _rgb:
        _new_rgb.append(
            (c / _max) * intensity
        )

    # Make sure all values under 255, which is the max supported number
    if exceed: 
        for i, x in enumerate(_new_rgb): 
            if x > 255:
                _new_rgb[i] = 255
        if all([i==255 for i in _new_rgb]):
            _new_rgb[2] = 254 # Allows white to be the largest colour, since #FFFFFF and #000000 aren't allowed
                
    return rgb_to_hex(_new_rgb)


# Dont ask me why, i dont know what the fuck this was made for
async def copy_context_with(ctx: commands.Context, *, author=None, channel=None, **kwargs):
    """
    Makes a new :class:`Context` with changed message properties.
    """

    # copy the message and update the attributes
    alt_message: discord.Message = copy.copy(ctx.message)
    alt_message._update(kwargs)  # pylint: disable=protected-access

    if author is not None:
        alt_message.author = author
    if channel is not None:
        alt_message.channel = channel

    # obtain and return a context of the same type
    return await ctx.bot.get_context(alt_message, cls=type(ctx))

def checklist_diff(data : dict):
    x = []
    for i, b in data.items():
        if b:
            x.append(f"+ {i}")
            continue
        x.append(f"- {i}")
    return "```diff\n{0}```".format(
        "\n".join(x)
    )