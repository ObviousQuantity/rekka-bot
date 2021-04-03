import discord
import asyncio
from discord import DMChannel
from discord.ext import commands, tasks
from typing import Optional
from datetime import datetime
from discord.ext.commands import CheckFailure
from discord.ext.commands import command, has_permissions, bot_has_permissions
from discord.ext.commands import Cog, Greedy
from datetime import datetime,timedelta
from discord import Embed, Member
import json

class Moderation(commands.Cog):

    def __init__(self,client):
        self.client = client

    @commands.command()
    async def test(self,ctx):
        await ctx.send("test")


    #Add words to the filter
    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def addword(self,ctx,*,word):
        with open("./data/server_settings.json","r") as f:
            filter = json.load(f)

        if word in filter[str(ctx.message.guild.id)]["filter"]:
            await ctx.send(f"**{word}** is already in the filter")
        else:
            filter[str(ctx.message.guild.id)]["filter"].append(word)
            await ctx.send(f"Added **{word}** to the swear filter")

        with open("./data/server_settings.json","w") as f:
            json.dump(filter,f,indent=4)

    #Remove words from the filter
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def removeword(self,ctx,*,word):
        with open("./data/server_settings.json","r") as f:
            filter = json.load(f)

        if word not in filter[str(ctx.message.guild.id)]["filter"]:
            await ctx.send(f"**{word}** is not in the filter")
        else:
            filter[str(ctx.message.guild.id)]["filter"].remove(word)
            await ctx.send(f"Removed **{word}** from the swear filter")

        with open("./data/server_settings.json","w") as f:
            json.dump(filter,f,indent=4)

    #View Filter
    @commands.command()
    async def viewfilter(self,ctx):

        with open("./data/server_settings.json","r") as f:
            filter = json.load(f)

        FilteredWords = filter[str(ctx.message.guild.id)]["filter"]

        try:
            embed = Embed(title = "Filter",
                          colour = ctx.guild.owner.colour)

            fields  = [("Current Words Being Filtered",'\n'.join(FilteredWords),False)]

            for name,value,inline in fields:
                embed.add_field(name = name, value = value, inline = inline)

            await ctx.send(embed=embed)
        except:
            await ctx.send("Couldnt get filter")

        with open("./data/server_settings.json","w") as f:
            json.dump(filter,f,indent=4)

    #Clear/Purge
    @commands.command(name = "clear", aliases = ["purge"], help = "deletes messages")
    @commands.bot_has_permissions(manage_messages = True)
    @commands.has_permissions(manage_messages = True)
    async def clear_messages(self,ctx,targets: Greedy[Member],limit: int = 1):
        def _check(message):
            return not len(targets) or message.author in targets

        if 0 < limit <= 100:
            with ctx.channel.typing():
                await ctx.message.delete()
                deleted = await ctx.channel.purge(limit=limit,check=_check)

                await ctx.send(f"Deleted {len(deleted):,} messages",delete_after = 5)
        else:
            await ctx.send("The limit provided is not within acceptable bounds")

    #Nuke
    @commands.command(name = "nuke",help = "deletes the chanel and readds it")
    @commands.has_permissions(manage_messages=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        if channel == None: 
            await ctx.send("You did not mention a channel!")
            return

        nuke_channel = discord.utils.get(ctx.guild.channels, name=channel.name)

        if nuke_channel is not None:
            new_channel = await nuke_channel.clone(reason="Has been Nuked!")
            await nuke_channel.delete()
            await new_channel.send("THIS CHANNEL HAS BEEN NUKED!")
            await ctx.send("Nuked the Channel sucessfully!")

        else:
            await ctx.send(f"No channel named {channel.name} was found!")

    #Kick
    @command(name = "kick")
    @bot_has_permissions(kick_members = True)
    @has_permissions(kick_members = True)
    async def kick(self,ctx,targets: Greedy[Member],*,reason: Optional[str] = "No reason provided"):
        if not len(targets):
            await ctx.send("One or more required arguments are missing")
        else:
            for target in targets:
                #Checks if the role of the bot is higher and make sure the target is not an admin
                if (ctx.guild.me.top_role.position > target.top_role.position and not target.guild_permissions.administrator):
                    await target.kick(reason = reason)

                    embed = Embed(title = "Member Kicked",
                                  colour = 0xDD2222,
                                  timestamp = datetime.utcnow())

                    embed.set_thumbnail(url = target.avatar_url)

                    fields = [("Member",f"{target.name} a.k.a {target.display_name}",False),
                              ("Kicked By", ctx.author.display_name,False),
                              ("Reason",reason,False)]

                    for name,value,inline in fields:
                        embed.add_field(name = name, value = value, inline = inline)

                    await ctx.send(embed = embed)

                else:
                    await ctx.send(f"{target.display_name} could not be kicked")

    #Mute
    @command(name = "mute")
    @bot_has_permissions(manage_roles = True)
    @has_permissions(manage_roles = True,manage_guild = True)
    async def mute(self,ctx,targets:Greedy[Member],hours:Optional[int],*,reason:Optional[str]):
        mute_role = discord.utils.get(ctx.guild.roles,name="mute")

        if not len(targets):
            await ctx.send("One or more required arguments are missing")

        else:

            #Check if the mute role exisits
            if not mute_role:
                try:
                    mute_role = await ctx.guild.create_role(name="mute")

                    for channel in ctx.guild.channels:
                        await channel.set_permissions(mute_role,speak=False,send_messages=False,
                                                     read_message_history=True,read_messages=False)

                except discord.Forbidden:
                    ctx.send("There is no mute role and I'm unable to create one")
                    return

            unmutes = []

            for target in targets:
                if not mute_role in target.roles:
                    if ctx.guild.me.top_role.position > target.top_role.position:
                        role_ids = ",".join([str(r.id) for r in target.roles])
                        end_time = datetime.utcnow() + timedelta(seconds=hours) if hours else None

                        await target.edit(roles=[mute_role])
                        #await ctx.target.add_roles(role)

                        embed = Embed(title = "Member Muted",
                                      colour = ctx.guild.owner.colour,
                                      timestamp = datetime.utcnow())

                        embed.set_thumbnail(url = target.avatar_url)

                        fields = [("Member",target.display_name,False),
                                  ("Muted By",ctx.author.display_name,False),
                                  ("Duration",f"{hours:,}hour(s)" if hours else "Indefinite",False),
                                  ("Reason",reason,False)]

                        for name,value,inline in fields:
                            embed.add_field(name=name,value=value,inline=inline)

                        await ctx.send(embed=embed)

                        if hours:
                            unmutes.append(target)
                    else:
                        await ctx.send(f"{target.display_name} could not be muted")
                else:
                    await ctx.send(f"{target.display_name} is already muted")

            await ctx.send("Action complete")

            if len(unmutes):
                await asyncio.sleep(hours)
                await self.unmute(ctx,targets)

    async def unmute(self,ctx,targets):
        print("UNMUTE")
        mute_role = discord.utils.get(ctx.guild.roles,name="mute")
        for target in targets:
            if mute_role in target.roles:
                await target.remove_roles(mute_role)

    #Unmute
    @command(name = "unmute")
    @bot_has_permissions(manage_roles = True)
    @has_permissions(manage_roles = True,manage_guild = True)
    async def unmute_command(self,ctx,targets:Greedy[Member]):
        if not len(targets):
            await ctx.send("One or more required arguments is missing")

        else:
            await self.unmute(ctx,targets)

    #Ban
    @command(name = "ban")
    @bot_has_permissions(ban_members = True)
    @has_permissions(ban_members = True)
    async def ban(self,ctx,targets: Greedy[Member],*,reason: Optional[str] = "No reason provided"):
        if not len(targets):
            await ctx.send("One or more required arguments are missing")
        else:
            for target in targets:
                #Checks if the role of the bot is higher and make sure the target is not an admin
                if (ctx.guild.me.top_role.position > target.top_role.position and not target.guild_permissions.administrator):
                    await target.ban(reason = reason)

                    embed = Embed(title = "Member Banned",
                                  colour = 0xDD2222,
                                  timestamp = datetime.utcnow())

                    embed.set_thumbnail(url = target.avatar_url)

                    fields = [("Member",f"{target.name} a.k.a {target.display_name}",False),
                              ("Banned By", ctx.author.display_name,False),
                              ("Reason",reason,False)]

                    for name,value,inline in fields:
                        embed.add_field(name = name, value = value, inline = inline)

                    await ctx.send(embed = embed)

                else:
                    await ctx.send(f"{target.display_name} could not be banned")

    #Unban
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self,ctx,*,member:discord.Member):
           banned_users = await ctx.guild.bans()
           member_name, member_discriminator = member.split("#")

           for ban_entry in banned_users:
               user = ban_entry.user

               if (user.name,user.discriminator) == (member_name,member_discriminator):
                   await ctx.guild.unban(user)
                   await ctx.send(f"Unbanned {user.mention}")
                   return


        
def setup(client):
   client.add_cog(Moderation(client))

