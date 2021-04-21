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
import asyncio
import motor.motor_asyncio
from discord.ext import commands, tasks
from discord import Embed, Member
from discord import Intents, DMChannel

#Local Code
import utils.json_loader
from utils.mongo import Document
from cogs import moderation

#idk what to do with these
import json
from random import choice
from glob import glob
from datetime import datetime
from re import search

cwd = Path(__file__).parents[0]
cwd = str(cwd)
#print(f"{cwd}\n-----------------------------")
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
#bot.connection_url = os.environ["MONGO"] #Use when running on Heroku
bot.connection_url = secret_file["mongo"]

bot.colors = {
    "WHITE": 0xFFFFFF,
    "AQUA": 0x1ABC9C,
    "GREEN": 0x2ECC71,
    "BLUE": 0x3498DB,
    "PURPLE": 0x9B59B6,
    "LUMINOUS_VIVID_PINK": 0xE91E63,
    "GOLD": 0xF1C40F,
    "ORANGE": 0xE67E22,
    "RED": 0xE74C3C,
    "NAVY": 0x34495E,
    "DARK_AQUA": 0x11806A,
    "DARK_GREEN": 0x1F8B4C,
    "DARK_BLUE": 0x206694,
    "DARK_PURPLE": 0x71368A,
    "DARK_VIVID_PINK": 0xAD1457,
    "DARK_GOLD": 0xC27C0E,
    "DARK_ORANGE": 0xA84300,
    "DARK_RED": 0x992D22,
    "DARK_NAVY": 0x2C3E50,
}
bot.color_list = [c for c in bot.colors.values()]

@bot.event
async def on_ready():

    print("--------------------")
    print('Logged in as {0.user}'.format(bot))
    print("Bot is in " + str(len(bot.guilds)) + " server(s)")
    print("--------------------")

    await bot.change_presence(activity=discord.Game(name="Test"))
    """Other Statuses
    await bot.change_presence(activity=discord.Streaming(name="My Stream", url="https://www.twitch.tv/jardius"))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="a song"))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="a movie"))
    """
    #Remove any data from servers the bot was removed from when it was offline
    for document in await bot.config.get_all():
        if not bot.get_guild(document["_id"]):
            await bot.config.delete_by_id(document["_id"])

    #Add any data to servers the bot is now in while it was offline
    for guild in bot.guilds:
        if not await bot.config.find(guild.id):
            await bot.config.upsert({"_id": guild.id})
    """
    for document in await bot.config.get_all():
        print(document)
    """
    for cog in os.listdir("./Rekka/cogs"):
        if cog.endswith(".py"):
            try:
                bot.load_extension(f"cogs.{cog[:-3]}")
                print(f" {cog} Loaded")
            except:
                print(f"Failed to load {cog}")

@bot.event
async def on_member_remove(member):
    print("Member Left")

@bot.event
async def on_member_join(member):
    print("Member Joined")

@bot.event 
async def on_reaction_add(reaction,user):
    print("Reaction Added")

@bot.event
async def on_guild_remove(guild):
    print("Bot Removed From Server")

    if await bot.config.find(guild.id):
        await bot.config.delete_by_id(guild.id)
        print("Removed Data")

@bot.event
async def on_guild_join(guild):
    print("Bot Joined A Server")

    if not await bot.config.find(guild.id):
        await bot.config.upsert({"_id": guild.id})
        print("Created Data")

    channels = guild.text_channels

    #Pick a random channel to send thank you message
    if not channels == 0:
        await choice(channels).send("Thanks for inviting me")

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

        if isinstance(message.channel,DMChannel):
            #MODMAIL
            guild_id = message.content.split()[0] #this gets the guild id the user specified and saves it in a variable
            question = message.content.split(guild_id)[1] #the question/message
            if not guild_id or not question:
                embed = Embed(title = "Modmail",
                colour = bot.colors.get("BLUE"),
                description = "Please respond with the **ID** of the server you want to send a ticket too along with your **message**. <ID> <Message>")

                for guild in bot.guilds:
                    embed.add_field(name=guild.name, value="ID: "+str(guild.id), inline=True)

                await ctx.send(embed=embed)
                return

            if await bot.config.find(int(guild_id)):
                data = await bot.config.find(int(guild_id))
                if data and "modmail_channel_id" in data:
                    modmail_channel_id = data["modmail_channel_id"]
                    modmail_channel = bot.get_channel(modmail_channel_id)

                    embed = Embed(title = "Modmail",
                                colour = message.author.colour,
                                timestamp = datetime.utcnow())

                    embed.set_thumbnail(url = message.author.avatar_url)

                    fields = [("Member",message.author.display_name,False),
                                ("Message",question,False)]

                    for name,value,inline in fields:
                        embed.add_field(name = name, value = value, inline = inline)

                    await modmail_channel.send(embed=embed)
    
                    #finally we're going to notify the user that his request has been successfully recieved
                    await message.channel.send(f"Message successfully sent to `{guild_id}`!")
            else:
                await message.channel.send(f"Couldn't send message")
        else:
            #ANTI-SPAM
            if len(list(filter(lambda m: check(m),bot.cached_messages))) >= 6: 
                await message.channel.send("Don't spam!",delete_after=5)
                unmutes = await moderation.Moderation.mute_members(bot,message,[message.author],5,reason="Spam")

                if len(unmutes):
                    await asyncio.sleep(5)
                    await moderation.Moderation.unmute_members(bot,ctx.guild,[message.author])

            #CHAT FILTER
            #This probably isn't the way to do this, but I wanna ignore these commands
            ignore = ["removeword","play","addword"] #Commands to ignore
            if not str(ctx.command) in ignore:
                data = await bot.config.find(message.guild.id)
                if not data or "filter" not in data:
                    await bot.config.upsert({"_id": message.guild.id, "filter": []})
                    data = await bot.config.find(message.guild.id) #Get the dat data again
                filteredwords = data["filter"]
                if not filteredwords == 0:
                    for word in filteredwords:
                        if message.content.count(word) > 0:
                            await message.delete()
                            try:
                                await message.author.send(f'Your message was deleted because it contained a blacklisted word **{word}**')
                            except:
                                await message.channel.send(f"{message.author.mention} your message was deleted because it contained a blacklisted word **{word}**")

    await bot.process_commands(message)


if __name__ == "__main__":
    bot.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(bot.connection_url))
    bot.db = bot.mongo["dbName"]
    bot.config = Document(bot.db, "collectionName")
    print("Database Initalized")
    #bot.run(os.environ["TOKEN"]) #Use when running on Heroku
    bot.run(bot.token)