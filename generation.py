"""
Copyright 2021 crazygmr101

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the 
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit 
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the 
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE 
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import asyncio
from io import BytesIO
from typing import OrderedDict, Tuple

import aiohttp
import restcord
from PIL import Image, ImageDraw, ImageChops, ImageFont
from expiringdict import ExpiringDict

lock = asyncio.Lock()
av_cache: OrderedDict[int, Image.Image] = ExpiringDict(max_age_seconds=60 * 30, max_len=100)


def crop_to_circle(im):
    big_size = (im.size[0] * 3, im.size[1] * 3)
    mask = Image.new('L', big_size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + big_size, fill=255)
    mask = mask.resize(im.size, Image.ANTIALIAS)
    mask = ImageChops.darker(mask, im.split()[-1])
    im.putalpha(mask)


def convert_color(clr: str) -> Tuple[int, int, int]:
    red = int(clr[0:2], 16)
    green = int(clr[2:4], 16)
    blue = int(clr[4:6], 16)
    return red, green, blue

async def welcome(user: restcord.User, invite: restcord.Invite, color: str, color2: str) -> BytesIO:
    if user.id not in av_cache:
        async with lock:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.png?size=128") as resp:
                    buf = BytesIO()
                    buf.write(await resp.read())
                    av_cache[user.id] = Image.open(buf, formats=["png"])
                    av_cache[user.id].load()
                    crop_to_circle(av_cache[user.id])

    image = Image.new("RGBA", (768, 256), convert_color(color))
    image_draw = ImageDraw.Draw(image)
    image_draw.ellipse((57, 57, 199, 199), convert_color(color2))
    image.alpha_composite(av_cache[user.id], (64, 64))

    server_text = f"Welcome to {invite.guild.name}, "
    server_font = ImageFont.truetype("Ubuntu-R.ttf", 48)
    size = 48
    while server_font.getsize(server_text)[0] > 484:
        server_font = ImageFont.truetype("Ubuntu-R.ttf", size := size - 1)
    # 256 + 14 = 270
    # 768 - 14 = 754
    # center on 484
    width, height = server_font.getsize(server_text)
    image_draw.text((484-width/2, 128-(height+5)), server_text, font=server_font, fill=convert_color(color2))

    user_text = f"{user.name}#{user.discriminator}"
    user_font = ImageFont.truetype("Ubuntu-R.ttf", 64)
    size = 64
    while user_font.getsize(user_text)[0] > 484:
        user_font = ImageFont.truetype("Ubuntu-R.ttf", size := size - 1)
    # 256 + 14 = 270
    # 768 - 14 = 754
    # center on 484
    width, height = user_font.getsize(user_text)
    image_draw.text((484-width/2, 128+5), user_text, font=user_font, fill=convert_color(color2))

    io = BytesIO()
    image.save(io, "PNG")
    io.seek(0)
    return io
