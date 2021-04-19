"""
Just so I don't forget how to do this
git rm -r --cached .
git add .
git status
git commit -am 'Removed files from the index (now ignored)'
git push
"""
#Standard Libraries
import contextlib
import io
import os
import logging

#Third Party Libraries
import textwrap
from traceback import format_exception

import discord
from pathlib import Path
import motor.motor_asyncio
from discord.ext import commands, tasks

#Local Code
import utils.json_loader
from utils.mongo import Document

#idk what to do with these
import json
from discord import Intents, DMChannel
from random import choice
from glob import glob
from datetime import datetime
from discord import Embed, Member
from re import search
from cogs import moderation
import asyncio

cwd = Path(__file__).parents[0]
cwd = str(cwd)
print(f"{cwd}\n-----------------------------")

cogs = [path.split("\\")[-1][:-3] for path in glob("./Rekka/cogs/*.py")]

async def get_prefix(bot, message):
    # If dm's
    if not message.guild:
        return commands.when_mentioned_or(bot.default_prefix)(bot, message)

    try:
        data = await bot.config.find(message.guild.id)

        # Make sure we have a useable prefix
        if not data or "prefix" not in data:
            return commands.when_mentioned_or(bot.default_prefix)(bot, message)
        return commands.when_mentioned_or(data["prefix"])(bot, message)
    except:
        return commands.when_mentioned_or(bot.default_prefix)(bot, message)

intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.messages = True
intents.guilds = True
default_prefix = "."
secret_file = utils.json_loader.read_json("secrets")
bot = commands.Bot(
    command_prefix = get_prefix,
    case_insenitive = True,
    intents = intents,
)
bot.default_prefix = default_prefix
bot.token = secret_file["token"]
bot.connection_url = os.environ["MONGO"] #Use when running on Heroku
#bot.connection_url = secret_file["mongo"]

@bot.event
async def on_ready():

    print("--------------------")
    print('Logged in as {0.user}'.format(bot))
    print("Bot is in " + str(len(bot.guilds)) + " server(s)")
    print("--------------------")

    await bot.change_presence(activity=discord.Game(name="Test"))
    """
    await bot.change_presence(activity=discord.Streaming(name="My Stream", url="https://www.twitch.tv/jardius"))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="a song"))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="a movie"))
    """
    for document in await bot.config.get_all():
        print(document)

    for cog in os.listdir("./Rekka/cogs"):
        if cog.endswith(".py"):
            try:
                bot.load_extension(f"cogs.{cog[:-3]}")
                print(f" {cog} Loaded")
            except:
                print(f"Failed to load {cog}")

@bot.event
async def on_message(message):

    ctx = await bot.get_context(message)

    def check(msg):
        return (msg.author == message.author
                and (datetime.utcnow()-msg.created_at).seconds < 30)    

    """
    url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

    if search(url_regex,message.content):
        await message.delete()
        await message.channel.send("You can't send links in this channel")

    if any([hasattr(a,"width") for a in message.attachments]):
        await message.delete()
        await message.channel.send("You can't send images here",delete_after=10)
    """

    if not message.author.bot:

        if len(list(filter(lambda m: check(m),bot.cached_messages))) >= 6: 
               await message.channel.send("Don't spam!",delete_after=5)
               unmutes = await moderation.Moderation.mute_members(bot,message,[message.author],5,reason="Spam")

               if len(unmutes):
                   await asyncio.sleep(5)
                   await moderation.Moderation.unmute_members(bot,ctx.guild,[message.author])

        if isinstance(message.channel,DMChannel):

            #if message.content.startswith("?request"):
            try:
                server_name = message.content.split()[0] #this gets the server name the user specified and saves it in a variable
                question = message.content.split()[1] #the question/message
                text = message.content.split(server_name)
                user_request = text[1]
            except:
                embed = Embed(title = "Modmail",
                             colour = 0x3498db,
                             description = "Please respond with the **ID** of the server you want to send a ticket too along with your **message**. <ID> <Message>")

                for guild in bot.guilds:
                    embed.add_field(name=guild.name, value="ID: "+str(guild.id), inline=True)

                await ctx.send(embed=embed)
                return

            json_file = open("./data/server_settings.json").read()
            servers = json.loads(json_file)

            try:
                get_channel_from_server = servers[server_name]["modmail_channel_id"]
                get_channel = bot.get_channel(int(get_channel_from_server))

                embed = Embed(title = "Modmail",
                              colour = message.author.colour,
                              timestamp = datetime.utcnow())

                embed.set_thumbnail(url = message.author.avatar_url)

                fields = [("Member",message.author.display_name,False),
                            ("Message",user_request,False)]

                for name,value,inline in fields:
                    embed.add_field(name = name, value = value, inline = inline)

                await get_channel.send(embed=embed)
 
                #finally we're going to notify the user that his request has been successfully recieved
                await message.channel.send(f"Message successfully sent to `{server_name}`!")
            except:
                await message.channel.send(f"The server `{server_name}` is not a valid server or doesnt have a modmail channel.")

        else:
            if not str(ctx.command) == "removeword":
                if not str(ctx.command) == "play":
                    if not str(ctx.command) == "addword":
                        if message.guild:
                            data = await bot.config.find(message.guild.id)
                            if not data or "filter" not in data:
                                await bot.config.upsert({"_id": message.guild.id, "filter": []})
                                data = await bot.config.find(message.guild.id)
                            bad_words = data["filter"]
                            if not bad_words == 0:
                                for word in bad_words:
                                    if message.content.count(word) > 0:
                                        await message.delete()
                                        try:
                                            await message.author.send(f'Tour message was deleted because it contained a blacklisted word **{word}**')
                                        except:
                                            await message.channel.send(f"{message.author.mention} your message because it contained a blacklisted word **{word}**")
                                        return

    await bot.process_commands(message)


if __name__ == "__main__":
    bot.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(bot.connection_url))
    bot.db = bot.mongo["dbName"]
    bot.config = Document(bot.db, "collectionName")
    bot.run(os.environ["TOKEN"]) #Use when running on Heroku
    #bot.run(bot.token)