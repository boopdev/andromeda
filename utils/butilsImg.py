import discord, math, io
from discord.ext import commands

from PIL import Image, ImageDraw, ImageColor
import PIL

async def make_progress_bar(client, progress : float, _max : float = 100, color : int = 0xd285fc):
    color_str = "#" + str(hex(color))[2:]
    r = await client.loop.run_in_executor(None, pillow_progress_bar, progress, _max, color_str)
    return r

def pillow_progress_bar(progress : float, _max : float, color_str : str = "#d285fc"):
    if _max < progress: raise ValueError("Progress greater than max value")


    im = Image.new(
        "RGB", (1000, 20),
        color="#4f545c"
    )

    draw = ImageDraw.Draw(im)
    draw.rectangle(
        [(
            0,
            0
        ),
        (
            math.floor(im.size[0] * (progress/_max)), # X
            im.size[1] # Y
        )],
        fill = color_str
    )

    with io.BytesIO() as out:
        im.save(out, format='JPEG')
        out.seek(0)
        return discord.File(fp=out, filename='progressbar.jpeg')
