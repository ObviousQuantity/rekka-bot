"""
Just so I don't forget how to do this
git rm -r --cached .
git add .
git status
git commit -am 'Removed files from the index (now ignored)'
git push
"""

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
from cogs import moderation
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

    #Statuses
    # Setting `Playing ` status
    await bot.change_presence(activity=discord.Game(name="Message me for modmail!"))

    # Setting `Streaming ` status
    #await bot.change_presence(activity=discord.Streaming(name="My Stream", url="https://www.twitch.tv/jardius"))

    # Setting `Listening ` status
    # await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="a song"))

    # Setting `Watching ` status
    #await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="a movie"))

@bot.event
async def on_guild_join(guild):
    print("Rekka Joined A Server")

    channels = guild.text_channels

    #Pick a random channel to send thank you message
    if channels == 0:
        await guild.owner.send("You don't have any channels")
    else:
       await choice(channels).send("Thanks for inviting me")

    with open("./data/server_settings.json","r") as f:
        settings = json.load(f)

    settings[guild.id] = {}
    settings[guild.id]["prefix"] = "."
    settings[guild.id]["filter"] = []
    settings[guild.id]["logs_channel"] = ""
    settings[guild.id]["modmail_channel"] = ""
    settings[guild.id]["welcome_message"] = []
    settings[guild.id]["goodbye_message"] = []
    settings[guild.id]["join_roles"] = []
    settings[guild.id]["welcome_channel"] = ""
    settings[guild.id]["goodbye_channel"] = ""
    
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

    server_id = str(member.guild.id)

    if member != bot:

        with open("./data/server_settings.json","r") as f:
            settings = json.load(f)

        #Welcome Message
        #Check if welcome_channel is in the setting json for the server
        #Then check if it doesn't equal ""
        #Then check if welcome_message is in the setting json for the server
        #Then check if the list doesn't equal 0
        #Then randomly select a welcome message from the list to send
        if "welcome_channel" in settings[server_id]:
            if settings[server_id]["welcome_channel"] != "":
                welcome_channel = int(settings[server_id]["welcome_channel"])

                if "welcome_message" in settings[server_id]:
                    if len(settings[guild.id]["welcome_message"]) != 0:
                        welcome__message = choice(settings[guild.id]["welcome_message"])
                        await bot.get_channel(server_id).send(f"{welcome__message}")
                else:
                    print("Server doesn't have welcome_message in settings json")
                    settings[guild.id]["welcome_message"] = []
        else:
            print("Server doesn't have welcome_channel in settings json")
            settings[server_id]["welcome_channel"] = ""

        #Auto Role
        #Check if join_roles is in the settings json for the server
        #Then check if it doesn't equal 0
        #Then for each role in the list add it to the player
        if "join_roles" in settings[server_id]:
            if len(settings[server_id]["join_roles"]) != 0:
                for role_name in settings[server_id]["join_roles"]:
                    try:
                        role = discord.utils.get(member.guild.roles,name=role_name)
                        await member.add_roles(role)
                    except:
                        print("Couldn't Get Role / Couldn't Add Role")
        else:
            print("Server doesn't have join_roles in settings json")
            settings[server_id]["join_roles"] = []

        with open("./data/server_settings.json","w") as f:
            json.dump(settings,f,indent=4)

@bot.event
async def on_member_remove(member):
    print("Member Left")

    server_id = str(member.guild.id)

    if member != bot:

        with open("./data/server_settings.json","r") as f:
            settings = json.load(f)

        #Welcome Message
        #Check if welcome_channel is in the setting json for the server
        #Then check if it doesn't equal ""
        #Then check if welcome_message is in the setting json for the server
        #Then check if the list doesn't equal 0
        #Then randomly select a welcome message from the list to send
        if "goodbye_channel" in settings[server_id]:
            if settings[server_id]["goodbye_channel"] != "":
                welcome_channel = int(settings[server_id]["goodbye_channel"])

                if "goodbye_message" in settings[server_id]:
                    if len(settings[guild.id]["goodbye_message"]) != 0:
                        goodbye_message = choice(settings[guild.id]["goodbye_message"])
                        await bot.get_channel(server_id).send(f"{goodbye_message}")
                else:
                    print("Server doesn't goodbye_message in settings json")
                    settings[server_id]["goodbye_message"] = []
        else:
            print("Server doesn't have goodbye_channel in settings json")
            settings[server_id]["goodbye_channel"] = ""

        with open("./data/server_settings.json","w") as f:
            json.dump(settings,f,indent=4)

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
                            with open("./data/server_settings.json","r") as f:
                                settings = json.load(f)

                            bad_words = settings[str(message.guild.id)]["filter"]
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

is_prod = os.environ.get("IS_HEROKU",None)
if is_prod:
    print("ON HEROKU")
    bot.run(os.environ.get("TOKEN"))
else:
    print("NOT ON HEROKU")
    with open("data/token.0", "r", encoding="utf-8") as f:
        TOKEN = f.read()
    bot.run(TOKEN)
