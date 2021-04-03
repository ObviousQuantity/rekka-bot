import discord
import json
import os
from discord.ext import commands, tasks
from discord import Intents, DMChannel
from random import choice
from glob import glob
from datetime import datetime
from discord import Embed, Member
from re import search
import asyncio

cogs = [path.split("\\")[-1][:-3] for path in glob("./bot/cogs/*.py")]

def get_prefix(bot,message):

    if not isinstance(message.channel,DMChannel):
        with open("./data/server_settings.json","r") as f:
            settings = json.load(f)

            if settings[str(message.guild.id)]:
                return settings[str(message.guild.id)]["prefix"]
            else:
                return "."
    else:
        return "."

intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix=get_prefix,intents=intents)

#Runs when the bot comes online
@bot.event
async def on_ready():

    print("--------------------")
    print('We have logged in as {0.user}'.format(bot))
    print("Bot is in " + str(len(bot.guilds)) + " server(s)")
    print("--------------------")

    for cog in os.listdir("./bot/cogs"):
        if cog.endswith(".py"):
            try:
                bot.load_extension(f"cogs.{cog[:-3]}")
                print(f" {cog} Loaded")
            except:
                print(f"Failed to load {cog}")

    # Setting `Playing ` status
    await bot.change_presence(activity=discord.Game(name="Testing"))

    # Setting `Streaming ` status
    #await bot.change_presence(activity=discord.Streaming(name="My Stream", url="https://www.twitch.tv/jardius"))

    # Setting `Listening ` status
    # await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="a song"))

    # Setting `Watching ` status
    #await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="a movie"))

@bot.event
async def on_guild_join(guild):
    print("Bot Joined A Server")

    channels = guild.text_channels

    #Pick a random channel to send thank you message
    if channels == 0:
        await guild.owner.send("You don't have any channels")
    else:
       await choice(channels).send("Thanks for inviting me")

    with open("./utils/Server Settings.json","r") as f:
        settings = json.load(f)

    settings[guild.id] = {}
    settings[guild.id]["prefix"] = "."
    settings[guild.id]["filter"] = []
    settings[guild.id]["logs_channel"] = ""
    settings[guild.id]["modmail_channel"] = ""
    
    with open("./data/server_settings.json","w") as f:
        json.dump(settings,f,indent=4)

@bot.event
async def on_guild_remove(guild):
    print("Bot Removed From Server")

    with open("./data/server_settings.json","r") as f:
        settings = json.load(f)

    settings.pop(str(guild.id))
    
    with open("./data/server_settings.json","w") as f:
        json.dump(settings,f,indent=4)

@bot.event 
async def on_reaction_add(reaction,user):
    print("Reaction Added")

@bot.event
async def on_member_join(member):
    print("Member Joined")

    #await member.add_roles(*(member.guild.get_role(id_) for id_ in ()))

    #Add Roles
    role = discord.utils.get(member.guild.roles,name="Temp")
    if role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            pass
    else:
        pass

    await bot.get_channel(826874723509075978).send(f"Welcome {member.mention}!")

@bot.event
async def on_member_remove(member):
    print("Member Left")
    await bot.get_channel(826874741444050953).send(f"{member} left!")

@bot.event
async def on_message(message):
    ctx = await bot.get_context(message)
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

            #if message.content.startswith("?request"):
            try:
                server_name = message.content.split()[0] #this gets the server name the user specified and saves it in a variable
                question = message.content.split()[1] #the question/message
                text = message.content.split(server_name)
                user_request = text[1]
            except:
                await message.channel.send("Invalid Usage! Syntax: <serverID> <message>")
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
                            with open("./data/server_settings.json","r") as f:
                                filter = json.load(f)

                            bad_words = filter[str(message.guild.id)]["filter"]
                            if not bad_words == 0:
                                for word in bad_words:
                                    if message.content.count(word) > 0:
                                        await message.delete()
                                        try:
                                            await message.author.send(f'Tour message was deleted because it contained a blacklisted word **{word}**')
                                        except:
                                            await message.channel.send(f"{message.author.mention} your message because it contained a blacklisted word **{word}**")
                                        return

                            with open("./data/server_settings.json","w") as f:
                                json.dump(filter,f,indent=4)

    await bot.process_commands(message)

bot.run("ODIyNjI5Njk2MjI2OTgzOTM3.YFVDmw.cV9tp4alvmbTPE_z6yDEZKLKl68")
