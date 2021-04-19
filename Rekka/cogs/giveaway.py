import discord
import asyncio
import praw
from random import choice, randint
from typing import Optional
from discord.ext import commands, tasks
from discord.ext.commands import command, cooldown
from discord.ext.commands import BucketType
from discord import Member, Embed
from datetime import datetime,timedelta

def convert(time):
    pos = ["s","m","h","d"]
    time_dict = {"s":1,"m":60,"h":3600,"d":3600*24}
    unit = time[-1]

    if unit not in pos:
        return -1
    try:
        val = int(time[:-1])
    except:
        return 2

    return val * time_dict[unit]

class Giveaway(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.giveaways = []
       
    @commands.command(name = "creategiveaway",
                      description = "",
                      brief = "Create a giveaway",
                      aliases = ["setupgiveaway","sg","cg","giveaway","g"])
    async def create_giveaway(self,ctx):

        await ctx.send("Giveaway Creation. Answer each question within 30 seconds")

        questions = ["What channel should it be hosted in?",
                     "What should the duration be? (s|m|h|d)",
                     "What is the prize?"]

        answers = []

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        for i in questions:
            await ctx.send(i)

            try:
                message = await self.bot.wait_for("message",timeout=30.0,check=check)
            except asyncio.TimeoutError:
                await ctx.send("You didn't answer in time")
                return
            else:
                answers.append(message.content)

        # <#id> --> (<#)id(>)
        try:
            channel_id = int(answers[0][2:-1])
        except:
            await ctx.send(f"You didn't mention a channel")
            return

        channel = self.bot.get_channel(channel_id)

        time = convert(answers[1])
        if time == -1:
            await ctx.send(f"You didn't answer the time with a proper unit (s|m|h|d)")
            return
        elif time == -2:
            await ctx.send(f"The time must be an integer")

        prize = answers[2]

        await ctx.send(f"The giveaway will be in {channel.mention} and will last {answers[1]} seconds")

        embed = Embed(title="Giveaway",
                      description=prize,
                      colour=ctx.author.colour,
                      timestamp=datetime.utcnow())
        embed.add_field(name = "Hosted by:",value = ctx.author.mention)
        embed.set_footer(text = f"Ends {answers[1]} from now")

        embed_message = await channel.send(embed=embed)

        await embed_message.add_reaction("✅")

        await asyncio.sleep(time)

        message = await channel.fetch_message(embed_message.id)

        users = await message.reactions[0].users().flatten()
        users.pop(users.index(self.bot.user))
        
        winner = choice(users)

        await message.reply(f"The winner of the giveaway is {winner.mention}")

    @commands.command()
    async def reroll(self,ctx,channel:discord.TextChannel,id_:int):
        try:
            message = await channel.fetch_message(id_)
        except:
            await ctx.send("The id was entered incorrectly")
            return

        users = await message.reactions[0].users().flatten()
        users.pop(users.index(self.bot.user))

        winner = choice(users)

        await message.reply(f"The new winner of the giveaway is {winner.mention}")


def setup(bot):
   bot.add_cog(Giveaway(bot))


