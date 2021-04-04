import discord
import json
from time import time
from discord.ext import commands, tasks
from typing import Optional
from datetime import datetime
from discord.ext.commands import CheckFailure
from discord.ext.commands import command, has_permissions, bot_has_permissions
from discord.ext.commands import MissingPermissions
from discord.ext.commands import Cog, Greedy
from discord import Embed, Member
import random

"""
import discord
import json
import random
import datetime
from discord.ext import commands, tasks
"""

players = {}

class Utility(commands.Cog):

    def __init__(self,client):
        self.client = client

    #Ping
    @commands.command()
    async def ping(self,ctx):
        await ctx.message.add_reaction("👌")
        start = time()
        message = await ctx.send(f"Pong! \n Latency: {self.client.latency*1000:,.0f} ms.")
        end = time()

        await message.edit(content=f"Pong! \n Latency: {self.client.latency*1000:,.0f} ms. \n Response Time: {(end-start)*1000:,.0f} ms.")

    #User Info
    @command(name = "userinfo", aliases = ["ui","memberinfo","mi"])
    async def userinfo(self,ctx,target: Optional[Member]):
        target = target or ctx.author

        embed = Embed(title = "User Information",
                      colour = target.colour,
                      timestamp = datetime.utcnow())

        embed.set_thumbnail(url = target.avatar_url)

        fields = [("ID",target.id,False),
                  ("Name",str(target),True),
                  ("Bot?",target.bot,True),
                  ("Top Role",target.top_role.mention,True),
                  ("Status",str(target.status).title(),True),
                  ("Activity", f"{str(target.activity.type).split('.')[-1].title() if target.activity else 'N/A'} {target.activity.name if target.activity else ''}", True),
                  ("Created At",target.created_at.strftime("%d/%m/%Y %H:%M:%S"),True),
                  ("Joined At",target.joined_at.strftime("%d/%m/%Y %H:%M:%S"),True),
                  ("Boosted", bool(target.premium_since),True)]

        for name,value,inline in fields:
            embed.add_field(name = name, value = value, inline = inline)

        await ctx.send(embed = embed)

    #Server Info
    @command(name = "serverinfo", aliases = ["si","guildinfo","gi"])
    async def serverinfo(self,ctx):
        embed = Embed(title = "Server Information",
                      colour = ctx.guild.owner.colour,
                      timestamp = datetime.utcnow())

        embed.set_thumbnail(url = ctx.guild.icon_url)

        fields = [("ID", ctx.guild.id, True),
                 ("Owner", ctx.guild.owner, True),
                 ("Region", ctx.guild.region, True),
                 ("Created at", ctx.guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), True),
                 ("Members", len(ctx.guild.members), True),
                 ("Humans", len(list(filter(lambda m: not m.bot, ctx.guild.members))), True),
                 ("Bots", len(list(filter(lambda m: m.bot, ctx.guild.members))), True),
                 ("Banned members", len(await ctx.guild.bans()), True),
                 ("Text channels", len(ctx.guild.text_channels), True),
                 ("Voice channels", len(ctx.guild.voice_channels), True),
                 ("Categories", len(ctx.guild.categories), True),
                 ("Roles", len(ctx.guild.roles), True),
                 ("Invites", len(await ctx.guild.invites()), True),
                 ("\u200b", "\u200b", True)]

        for name,value,inline in fields:
            embed.add_field(name = name, value = value, inline = inline)

        await ctx.send(embed = embed)

    @command()
    @commands.has_permissions(administrator=True)
    async def load(self,ctx,extension):
        self.client.load_extension(f"cogs.{extension}")

    @command()
    @commands.has_permissions(administrator=True)
    async def unload(self,ctx,extension):
        self.client.unload_extension(f"cogs.{extension}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def changeprefix(self,ctx,prefix):
        with open("./data/server_settings.json","r") as f:
            prefixes = json.load(f)
            print(prefixes)

        print(prefixes[str(ctx.guild.id)]["prefix"])
        prefixes[str(ctx.guild.id)]["prefix"] = prefix
    
        with open("./data/server_settings.json","w") as f:
            json.dump(prefixes,f,indent=4)

        await ctx.send(f"Prefix changed to: {prefix}")

    @commands.command()
    async def passwordgenerator(self,ctx):
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()"

        def check(message):
            if message.content.isnumeric():
                print("number")
                return message.content
            else:
                print("not number")
                return 1

        password_len = await ctx.send("What length would you like your password to be?")
        response1 = await self.client.wait_for("message",check=check,timeout=5)
        password_count = await ctx.send("How many passwords would you like to create?")
        response2 = await self.client.wait_for("message",check=check,timeout=5)

        print(response1.content)
        print(response2.content)

        for x in range(0,int(response1.content)):
            password = ""
            for x in range(0,int(response2.content)):
                password_char = random.choice(chars)
                password = password + password_char
            await ctx.author.send("Your password: " + password)

    #Setup Modmail
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.command(name = "",
                      description = "Setup a modmail channel. When players message me"
                      " the messages will be logged here.",
                      brief = "setup a modmail channel",
                      aliases = ["setupmm"])
    async def setupmodmail(self,ctx):

        server_id = ctx.message.guild.id

        json_file = open("./data/server_settings.json").read()
        servers = json.loads(json_file)

        try:
            current_modmail_channel = await self.client.fetch_channel(int(servers[str(server_id)]["modmail_channel_id"]))
            await ctx.send("You already have a modmail channel setup")
            return
        except:
            try:
                if discord.utils.get(ctx.channels,name="modmail"):
                    channel = discord.utils.get(self.client.channels,name="modmail")
                    channel_id = channel.id
                    servers[str(server_id)]["modmail_channel_id"] = str(channel_id)
                else:
                    modmail_channel = await ctx.message.guild.create_text_channel("modmail")
                    servers[str(server_id)]["modmail_channel_id"] = str(modmail_channel.id)
            except discord.Forbidden:
                await ctx.send("Missing Permissions to create channels!")
                ctx.send("Missing Permissions to create channels!")
                return


        with open("./data/server_settings.json","w") as f:
            json.dump(servers,f,indent=4)

        await ctx.send("Successfully created a modmail channel")
        await modmail_channel.send("You will receive modmail here when users messaage me")

    #Setup Log
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.command(name = "",
                      description = "",
                      brief = "",
                      aliases = ["sl"])
    async def setuplogs(self,ctx):

        server_id = ctx.message.guild.id

        json_file = open("./data/server_settings.json").read()
        servers = json.loads(json_file)

        try:
            current_logs_channel = await self.client.fetch_channel(int(servers[str(server_id)]["logs_channel"]))
            await ctx.send("You already have a log channel setup")
            return
        except:
            try:
                if discord.utils.get(ctx.channels,name="logs"):
                    channel = discord.utils.get(self.client.channels,name="logs")
                    channel_id = channel.id
                    servers[str(server_id)]["modmail_channel_id"] = str(channel_id)
                else:
                    logs_channel = await ctx.message.guild.create_text_channel("logs")
                    servers[str(server_id)]["logs_channel"] = str(logs_channel.id)
            except discord.Forbidden:
                await ctx.send("Missing Permissions to create channels!")
                ctx.send("Missing Permissions to create channels!")
                return


        with open("./data/server_settings.json","w") as f:
            json.dump(servers,f,indent=4)

        await ctx.send("Successfully created a log channel")
        await logs_channel.send("Everything will be logged in this channel")

    #Give Role
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.command(name = "",
                      description = "",
                      brief = "",
                      aliases = ["gr"])
    async def giverole(self,ctx,member:discord.Member,role:discord.Role):
        #role = discord.utils.get(ctx.guild.roles,name=role_name)
        if role:
            try:
                await member.add_roles(role)
                await ctx.send(f"Successfully given the **{role}** to {member}")
            except:
                await ctx.send(f"Couldn't add {role} to {member}")
        else:
            await ctx.send(f"The role **{role}** doesn't exisit")

    #Add Role
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.command(name = "",
                      description = "",
                      brief = "",
                      aliases = ["createrole","cr","ar"])
    async def addrole(self,ctx,*,role_name):
        if not discord.utils.get(ctx.guild.roles,name=role_name):
            try:
                await ctx.guild.create_role(name=role_name)
            except discord.Forbidden:
                await ctx.send("I don't have permission")
            await ctx.message.add_reaction("👌")
            await ctx.send(f"Created the role **{role_name}**")
        else:
            await ctx.send("A role with this name already exisits")

    #Delte Role
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.command(name = "",
                      description = "",
                      brief = "",
                      aliases = ["deleterole","ra","da"])
    async def removerole(self,ctx,*,arg):
        role = discord.utils.get(ctx.guild.roles, name=arg)
        if role:
            try:
              await role.delete()
              await ctx.send("The role {} has been deleted!".format(role.name))
            except discord.Forbidden:
              await ctx.send("Missing Permissions to delete this role!")
        else:
            await ctx.send("The role doesn't exist!")


def setup(client):
   client.add_cog(Utility(client))


