from pathlib import Path
from prsaw import RandomStuff

import json

import discord
from discord.ext import commands, tasks

def get_prefix(client,message):

    if not isinstance(message.channel,discord.DMChannel):
        with open("./data/server_settings.json","r") as f:
            settings = json.load(f)

            if settings[str(message.guild.id)]:
                return settings[str(message.guild.id)]["prefix"]
            else:
                return "."
    else:
        return "."

rs = RandomStuff(async_mode=True)
intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True)

class Rekka(commands.Bot):
    def __init__(self):
        self._cogs = [p.stem for p in Path(".").glob("./bot/cogs/*.py")]
        super().__init__(command_prefix=get_prefix,intents=intents)

    def setup(self):
        print("Running setup...")

        for cog in self._cogs:
            self.load_extension(f"bot.cogs.{cog}")
            print(f" Loaded `{cog}` cog.")

        print("Setup complete.")

    def run(self):
        self.setup()

        with open("data/token.0", "r", encoding="utf-8") as f:
            TOKEN = f.read()

        print("Running bot...")
        super().run(TOKEN, reconnect=True)

    async def shutdown(self):
        print("Closing connection to Discord...")
        await super().close()

    async def close(self):
        print("Closing on keyboard interrupt...")
        await self.shutdown()

    async def on_connect(self):
        print(f" Connected to Discord (latency: {self.latency*1000:,.0f} ms).")

    async def on_resumed(self):
        print("Bot resumed.")

    async def on_disconnect(self):
        print("Bot disconnected.")

    # async def on_error(self, err, *args, **kwargs):
    #     raise

    # async def on_command_error(self, ctx, exc):
    #     raise getattr(exc, "original", exc)

    async def on_ready(self):
        self.client_id = (await self.application_info()).id
        print("Bot ready.")

    async def process_commands(self, msg):
        ctx = await self.get_context(msg, cls=commands.Context)

        if ctx.command is not None:
            await self.invoke(ctx)
            
    async def on_guild_join(self,guild):
        print("Bot Joined A Server")

    async def on_guild_remove(self,guild):
        print("Bot Removed From Server")

    async def on_member_join(self,ctx):
        print("Member Joined")
        role = discord.utils.get(ctx.guild.roles,name="Test")
        await ctx.add_roles(role)

    async def on_reaction_add(self,reaction,user):
        print("Reaction Added")

    async def on_message(self,message):
        if not message.author.bot:

            if isinstance(message.channel,discord.DMChannel):
                print("Message Sent In DM")
                response = await rs.get_ai_response(message.content)
                await message.channel.send(response)
            else:
                print("Message Sent In Server")

            await self.process_commands(message)


