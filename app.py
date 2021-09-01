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
import os
import dotenv
from typing import OrderedDict

import expiringdict  # noqa
import quart
import restcord  # noqa

import generation


dotenv.load_dotenv()
lock = asyncio.Lock()
rc = restcord.RestCord(token=os.getenv("TOKEN"))
app = quart.Quart(import_name=__name__)
cache: OrderedDict[int, restcord.User] = expiringdict.ExpiringDict(max_len=10000, max_age_seconds=60 * 60)
invites: OrderedDict[str, restcord.Invite] = expiringdict.ExpiringDict(max_len=10000, max_age_seconds=60 * 60)


@app.get("/ping")
async def ping():
    return "Pong!", 200


@app.get("/coffee")
async def teapots_arent_for_coffee():
    return "Can't brew coffee in a teapot", 418


@app.get("/welcome-card/<int:user>/<string:invite>/<string:color>/<string:color2>")
async def welcome_card(user: int, invite: str, color: str, color2: str):
    if invite not in invites:
        async with lock:
            invites[invite] = await rc.invite_client.get_invite(invite)
    if user not in cache:
        async with lock:
            cache[user] = await rc.user_client.get_user(user)
    buf = await generation.welcome(cache[user], invites[invite], color, color2)

    async def img_generator():
        yield buf.read()
    return img_generator(), 200, {"Content-Type": "image/png"}


app.run(port=os.getenv("PORT"))
