from datetime import datetime
import discord
from discord import Embed
from discord.ext.commands import Cog
from discord.ext.commands import command

def get_guild(client,after):
	pass

class Log(Cog):
	def __init__(self, client):
		self.client = client

	@Cog.listener()
	async def on_user_update(self, before, after):

		log_channel = discord.utils.get(after.guild.text_channels, name="logs")

		if before.name != after.name:
			embed = Embed(title="Username change",
						  colour=after.colour,
						  timestamp=datetime.utcnow())

			fields = [("Before", before.name, False),
					  ("After", after.name, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			await channel.send(embed=embed)

		if before.discriminator != after.discriminator:
			embed = Embed(title="Discriminator change",
						  colour=after.colour,
						  timestamp=datetime.utcnow())

			fields = [("Before", before.discriminator, False),
					  ("After", after.discriminator, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			if log_channel != None:
				await log_channel.send(embed=embed)
			else:
				print("no log channel")

		if before.avatar_url != after.avatar_url:
			embed = Embed(title="Avatar change",
						  description="New image is below, old to the right.",
						  colour=self.log_channel.guild.get_member(after.id).colour,
						  timestamp=datetime.utcnow())

			embed.set_thumbnail(url=before.avatar_url)
			embed.set_image(url=after.avatar_url)

			if log_channel != None:
				await log_channel.send(embed=embed)
			else:
				print("no log channel")

	@Cog.listener()
	async def on_member_update(self, before, after):

		log_channel = discord.utils.get(after.guild.text_channels, name="logs")

		if before.display_name != after.display_name:
			embed = Embed(title="Nickname change",
						  colour=after.colour,
						  timestamp=datetime.utcnow())

			fields = [("Before", before.display_name, False),
					  ("After", after.display_name, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			if log_channel != None:
				await log_channel.send(embed=embed)
			else:
				print("no log channel")

		elif before.roles != after.roles:
			embed = Embed(title="Role updates",
						  colour=after.colour,
						  timestamp=datetime.utcnow())

			fields = [("Before", ", ".join([r.mention for r in before.roles]), False),
					  ("After", ", ".join([r.mention for r in after.roles]), False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			if log_channel != None:
				await log_channel.send(embed=embed)
			else:
				print("no log channel")

	@Cog.listener()
	async def on_message_edit(self, before, after):

		log_channel = discord.utils.get(after.guild.text_channels, name="logs")

		if not after.author.bot:
			if before.content != after.content:
				embed = Embed(title="Message edit",
							  description=f"Edit by {after.author.display_name}.",
							  colour=after.author.colour,
							  timestamp=datetime.utcnow())

				fields = [("Before", before.content, False),
						  ("After", after.content, False)]

				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)

				if log_channel != None:
					await log_channel.send(embed=embed)
				else:
					print("no log channel")

	@Cog.listener()
	async def on_message_delete(self, message):

		log_channel = discord.utils.get(message.guild.text_channels, name="logs")

		if not message.author.bot:
			embed = Embed(title="Message deletion",
						  description=f"Action by {message.author.display_name}.",
						  colour=message.author.colour,
						  timestamp=datetime.utcnow())

			fields = [("Content", message.content, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			if log_channel != None:
				await log_channel.send(embed=embed)
			else:
				print("no log channel")

def setup(client):
	client.add_cog(Log(client))

