import discord
import asyncio
import praw
from random import choice, randint
from typing import Optional
from discord.ext import commands, tasks
from discord.ext.commands import command, cooldown
from discord.ext.commands import BucketType
from discord import Member, Embed

reddit = praw.Reddit(client_id = "Hep_3WWz096efg",
                     client_secret = "8mbT11XiB6geg-nACN012JsmY1RXlg",
                     user_agent = "pythonpraw",
                     check_for_async=False)

class Fun(commands.Cog):

    def __init__(self,client):
        self.client = client

    @commands.command(
        description = "Description!",
        brief = "Sends a random spicy hot meme from r/memes"
        )
    @cooldown(1,10,BucketType.user)
    async def meme(self,ctx):

        submissions = reddit.subreddit("memes").hot()
        post_to_pick = randint(1,100)
        for i in range(0,post_to_pick):
            submission = next(x for x in submissions if not x.stickied)

        embed = Embed(title = submission.title,
                      colour = ctx.message.guild.owner.colour)
        embed.set_image(url=submission.url)
        embed.set_footer(text=f"Meme from r/memes")

        await ctx.send(embed=embed)

    @commands.command(name = "8ball",help = "ask a question")
    async def eightball(self,ctx,*,question):
        responses = ["It is certain.",
                    "It is decidedly so.",
                    "Without a doubt.",
                    "Yes - definitely.",
                    "You may rely on it.",
                    "As I see it, yes.",
                    "Most likely.",
                    "Outlook good.",
                    "Yes.",
                    "Signs point to yes.",
                    "Reply hazy, try again.",
                    "Ask again later.",
                    "Better not tell you now.",
                    "Cannot predict now.",
                    "Concentrate and ask again.",
                    "Don't count on it.",
                    "My reply is no.",
                    "My sources say no.",
                    "Outlook not so good.",
                    "Very doubtful."]
        await ctx.send(f"Question: {question}\nAnswer: {choice(responses)}")

    @commands.command(description='For when you wanna settle the score some other way')
    async def choose(self,ctx, *choices: str):
        """Chooses between multiple choices."""
        await ctx.send(choice(choices))

    @command(name = "dice",aliases = ["roll"])
    async def rolldice(self,ctx):
        message = await ctx.send("Choose a number:\n**4**, **6**, **8**, **10**, **12**, **20** ")
    
        def check(m):
            return m.author == ctx.author

        try:
            message = await self.client.wait_for("message", check = check, timeout = 30.0)
            m = message.content

            if m != "4" and m != "6" and m != "8" and m != "10" and m != "12" and m != "20":
                await ctx.send("Sorry, invalid choice.")
                return
        
            coming = await ctx.send("Here it comes...")
            await asyncio.sleep(1)
            await coming.delete()
            await ctx.send(f"**{randint(1, int(m))}**")
        except asyncio.TimeoutError:
            await message.delete()
            await ctx.send("Procces has been canceled because you didn't respond in **30** seconds.")

    @command(name = "slap",aliases = ["hit"])
    async def slapmember(self,ctx,member:Member,*,reason: Optional[str] = None):

        responses = [f"I clapped {member.mention} into next week"]

        if reason == None:
            await ctx.send(f"{choice(responses)}")
        else:
            await ctx.send(f"{ctx.author.display_name} slapped {member.mention} {reason}!")
       
def setup(client):
   client.add_cog(Fun(client))

