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
from utils.util import Pag
from copy import deepcopy
from dateutil.relativedelta import relativedelta

class Moderation(commands.Cog):

    def __init__(self,client):
        self.client = client
        self.mute_task = self.check_current_mutes.start()

    def cog_unload(self):
        self.mute_task.cancel()

    @tasks.loop(minutes=5)
    async def check_current_mutes(self):
        currentTime = datetime.now()
        mutes = deepcopy(self.client.muted_users)
        for key, value in mutes.items():
            if value["muteDuration"] is None:
                continue

            unmuteTime = value["mutedAt"] + relativedelta(seconds=value["muteDuration"])

            if currentTime >= unmuteTime:
                guild = self.client.get_guild(value["guildId"])
                member = guild.get_member(value["_id"])
                await self.unmute_members(guild,[member])

    @check_current_mutes.before_loop
    async def before_check_current_mutes(self):
        await self.client.wait_until_ready()

    #Gets The Log Channel From MongoDB
    async def get_log_channel(self,guild_id):
        data = await self.client.config.find(guild_id)
        if not data or "log_channel_id" not in data:
            print("No Log Channel")
            return False
        else:
            #Should probably check if the channel exisits
            print("Log Channel")
            return data["log_channel_id"] #Returns the channel id

    #Add words to the filter
    @commands.guild_only()
    @commands.command(name = "addword",
                      brief = "add a word from the filter",
                      aliases = ["aw"])
    @commands.has_permissions(manage_messages=True)
    async def addword(self,ctx,*,word):
        data = await self.client.config.find(ctx.guild.id)
        if not data or "filter" not in data:
            await self.client.config.upsert({"_id": ctx.guild.id, "filter": []})
            data = await self.client.config.find(ctx.guild.id)

        filteredwords = data["filter"]
        if word in filteredwords:
            await ctx.send(f"**{word}** is already in the filter")
        else:
            filteredwords.append(word)
            await self.client.config.upsert({"_id": ctx.guild.id, "filter": filteredwords})

    #Remove words from the filter
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.command(name = "removeword",
                      brief = "remove a word from the filter",
                      aliases = ["rw"])
    async def removeword(self,ctx,*,word):
        data = await self.client.config.find(ctx.guild.id)
        if not data or "filter" not in data:
            await self.client.config.upsert({"_id": ctx.guild.id, "filter": []})
            data = await self.client.config.find(ctx.guild.id)

        filteredwords = data["filter"]
        if word not in filteredwords:
            await ctx.send(f"**{word}** is not in the filter")
        else:
            filteredwords.remove(word)
            await self.client.config.upsert({"_id": ctx.guild.id, "filter": filteredwords})        

    #View Filter
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.command(name = "viewfilter",
                      brief = "view the words being filtered",
                      aliases = ["filter","f","vf"])
    async def viewfilter(self,ctx):
        data = await self.client.config.find(ctx.guild.id)
        filteredwords = data["filter"]

        try:
            embed = Embed(title = "Filter",
                            colour = 0x3498DB)

            fields  = [("Current Words Being Filtered",'\n'.join(filteredwords),False)]

            for name,value,inline in fields:
                embed.add_field(name = name, value = value, inline = inline)

            await ctx.send(embed=embed)
        except:
                embed=discord.Embed()
                embed.add_field(name="❌ Couldn't Get Filter", value=f"something went wrong or the list is empty. Use the **addword** command to filter a word", inline=False)
                await ctx.send(embed=embed)

    #Clear/Purge
    @commands.guild_only()
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
    @commands.guild_only()
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
    @commands.guild_only()
    @command(name = "kick")
    @bot_has_permissions(kick_members = True)
    @has_permissions(kick_members = True)
    async def kick(self,ctx,targets: Greedy[Member],*,reason: Optional[str] = "No reason provided"):

        if not len(targets):
            embed=discord.Embed()
            embed.add_field(name="❌ Missing Targets", value=f"please mention the people you wanna kick", inline=False)
            await ctx.send(embed=embed,delete_after=5)
            return

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
                    
                    #Get The Log Channel To Send A Message
                    log_channel_id = await self.get_log_channel(ctx.guild.id)
                    if log_channel_id != False:
                        log_channel = await self.client.fetch_channel(log_channel_id)
                        await log_channel.send(embed=embed)
                    else:
                        await ctx.send(embed=embed)

                else:
                    await ctx.send(f"{target.display_name} could not be kicked")

    #Mute Function
    async def mute_members(self,ctx,message,targets,hours,reason):

        mute_role = discord.utils.get(message.guild.roles,name="mute")
        #Check if the mute role exisits
        if not mute_role:
            try:
                mute_role = await message.guild.create_role(name="mute")

                for channel in message.guild.channels:
                    await channel.set_permissions(mute_role,speak=False,send_messages=False,
                                                   read_message_history=True,read_messages=False)

            except discord.Forbidden:
                return

        unmutes = []

        for target in targets:
            if not mute_role in target.roles:
                if message.guild.me.top_role.position > target.top_role.position:

                    data = {
                        "_id": target.id,
                        "mutedAt": datetime.now(),
                        "muteDuration": hours or None,
                        "mutedBy": ctx.author.id,
                        "guildId": ctx.guild.id,
                    }
                    await self.client.mutes.upsert(data)
                    self.client.muted_users[target.id] = data

                    #role_ids = ",".join([str(r.id) for r in target.roles])
                    #end_time = datetime.utcnow() + timedelta(seconds=hours) if hours else None

                    await target.edit(roles=[mute_role])
                    #await ctx.target.add_roles(role)

                    embed = Embed(title = "Member Muted",
                                    colour = message.guild.owner.colour,
                                    timestamp = datetime.utcnow())

                    embed.set_thumbnail(url = target.avatar_url)

                    fields = [("Member",target.display_name,False),
                                ("Muted By",message.author.display_name,False),
                                ("Duration",f"{hours:,}hour(s)" if hours else "Indefinite",False),
                                ("Reason",reason,False)]

                    for name,value,inline in fields:
                        embed.add_field(name=name,value=value,inline=inline)

                    #Get The Log Channel To Send A Message
                    log_channel_id = await self.get_log_channel(message.guild.id)
                    if log_channel_id != False:
                        try:
                            log_channel = await self.client.fetch_channel(log_channel_id)
                            await log_channel.send(embed=embed)
                        except:
                            pass

                    if hours:
                        unmutes.append(target)

        return unmutes

    #Mute
    @commands.guild_only()
    @command(name = "mute")
    @bot_has_permissions(manage_roles = True)
    @has_permissions(manage_roles = True,manage_guild = True)
    async def mute_command(self,ctx,targets:Greedy[Member],hours:Optional[int],*,reason:Optional[str]):
        
        if not len(targets):
            embed=discord.Embed()
            embed.add_field(name="❌ Missing Targets", value=f"please mention the people you wanna mute", inline=False)
            await ctx.send(embed=embed,delete_after=5)
            return
        else:
            unmutes = await self.mute_members(ctx,ctx.message,targets,hours,reason)

            if len(unmutes):
                await asyncio.sleep(hours)
                await self.unmute_members(ctx.guild,targets)

    #Unmute Function
    async def unmute_members(self,guild,targets,*,reason="Mute time expired."):
        mute_role = discord.utils.get(guild.roles,name="mute")
        for target in targets:
            if mute_role in target.roles:
                await target.remove_roles(mute_role)
            
            await self.client.mutes.delete(target.id)
            try:
                self.client.muted_users.pop(target.id)
            except KeyError:
                pass

    #Unmute
    @commands.guild_only()
    @command(name = "unmute")
    @bot_has_permissions(manage_roles = True)
    @has_permissions(manage_roles = True,manage_guild = True)
    async def unmute_command(self,ctx,targets:Greedy[Member],*,reason: Optional[str] = "No reason provided"):
        if not len(targets):
            embed=discord.Embed()
            embed.add_field(name="❌ Missing Targets", value=f"please mention the people you wanna mute", inline=False)
            await ctx.send(embed=embed,delete_after=5)
        else:
            await self.unmute_members(ctx.guild,targets,reason=reason)

    #Ban
    @commands.guild_only()
    @command(name = "ban")
    @bot_has_permissions(ban_members = True)
    @has_permissions(ban_members = True)
    async def ban(self,ctx,targets: Greedy[Member],*,reason: Optional[str] = "No reason provided"):

        if not len(targets):
            embed=discord.Embed()
            embed.add_field(name="❌ Missing Targets", value=f"please mention the people you wanna ban", inline=False)
            await ctx.send(embed=embed,delete_after=5)
            return

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

                    #Get The Log Channel To Send A Message
                    log_channel_id = await self.get_log_channel(ctx.guild.id)
                    if log_channel_id != False:
                        log_channel = await self.client.fetch_channel(log_channel_id)
                        await log_channel.send(embed=embed)
                    else:
                        await ctx.send(embed=embed)

                else:
                    await ctx.send(f"{target.display_name} could not be banned")

    #Unban
    @commands.guild_only()
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

    #Warning
    @commands.command()
    @commands.guild_only()
    #@cinnabds.has_role(roleid)
    async def warn(self,ctx,member:discord.Member,*,reason):
        # if member.id in [ctx.author.id, self.bot.user.id]:
        #     return await ctx.send("You cannot warn yourself or the bot")

        #How many warns they have
        current_warn_count = len(
            await self.client.warns.find_many_by_custom(
                {
                    "user_id": member.id, 
                    "guild_id": member.guild.id
                }
            )
        ) + 1

        warn_filter = {"user_id": member.id, "guild_id": member.guild.id, "number": current_warn_count}
        warn_data = {"reason": reason, "timestamp": ctx.message.created_at, "warned_by": ctx.author.id}

        await self.client.warns.upsert_custom(warn_filter,warn_data)

        embed = discord.Embed(
            title = "You've been warned!",
            description = f"__**Reason**__\n{reason}",
            colour = discord.Colour.red(),
            timestamp = ctx.message.created_at,
        )
        embed.set_author(name = ctx.guild.name, icon_url = ctx.guild.icon_url)
        embed.set_footer(text = f"Warns: {current_warn_count}")

        try:
            await member.send(embed=embed)
            await ctx.send("Warned that userin dm's")
        except discord.HTTPException:
            await ctx.send(member.mention,embed=embed)

    #Show Warns
    @commands.command()
    @commands.guild_only()
    async def warns(self, ctx, member:discord.Member):
        warn_filter = {"user_id": member.id, "guild_id": member.guild.id}
        warns = await self.client.warns.find_many_by_custom(warn_filter)

        if not bool(warns):
            return await ctx.send(f"Couldn't find any warns for {member.display_name}")

        warns = sorted(warns,key=lambda x: x["number"])

        pages = []
        for warn in warns:
            description = f"""
            Warn Number: `{warn['number']}`
            Warn Reason: `{warn['reason']}`
            Warned By: <@{warn['warned_by']}>
            Warn Number: {warn['timestamp'].strftime("%I:%M %p %B %d, %Y")}
            """
            pages.append(description)

        await Pag(
            title=f"Warns for `{member.display_name}`",
            colour=0xCE2029,
            entries=pages,
            length=1
        ).start(ctx)

def setup(client):
   client.add_cog(Moderation(client))

