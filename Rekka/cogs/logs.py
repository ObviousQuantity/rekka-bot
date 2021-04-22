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

	@Cog.listener()
	async def on_user_update(self, before, after):

		#Get The Log Channel
		log_channel_id = await self.get_log_channel(after.guild.id)

		if before.name != after.name:
			embed = Embed(title="Username change",
						  colour=before.color,
						  timestamp=datetime.utcnow())

			fields = [("Before", before.name, False),
					  ("After", after.name, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			if log_channel_id != False:
				try:
					log_channel = await self.client.fetch_channel(log_channel_id)
					await log_channel.send(embed=embed)
				except:
					pass

		if before.discriminator != after.discriminator:
			embed = Embed(title="Discriminator change",
						  colour=before.colour,
						  timestamp=datetime.utcnow())

			fields = [("Before", before.discriminator, False),
					  ("After", after.discriminator, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			if log_channel_id != False:
				log_channel = await self.client.fetch_channel(log_channel_id)
				await log_channel.send(embed=embed)

		if before.avatar_url != after.avatar_url:
			embed = Embed(title="Avatar change",
						  description="New image is below, old to the right.",
						  colour=before.color,
						  timestamp=datetime.utcnow())

			embed.set_thumbnail(url=before.avatar_url)
			embed.set_image(url=after.avatar_url)

			if log_channel_id != False:
				try:
					log_channel = await self.client.fetch_channel(log_channel_id)
					await log_channel.send(embed=embed)
				except:
					pass

	@Cog.listener()
	async def on_member_update(self, before, after):

		log_channel_id = await self.get_log_channel(after.guild.id)

		if before.display_name != after.display_name:
			embed = Embed(title="Nickname change",
						  colour=after.colour,
						  timestamp=datetime.utcnow())

			fields = [("Before", before.display_name, False),
					  ("After", after.display_name, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			if log_channel_id != False:
				log_channel = await self.client.fetch_channel(log_channel_id)
				await log_channel.send(embed=embed)

		elif before.roles != after.roles:
			embed = Embed(title="Role updates",
						  colour=after.colour,
						  timestamp=datetime.utcnow())

			fields = [("Before", ", ".join([r.mention for r in before.roles]), False),
					  ("After", ", ".join([r.mention for r in after.roles]), False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			if log_channel_id != False:
				try:
					log_channel = await self.client.fetch_channel(log_channel_id)
					await log_channel.send(embed=embed)
				except:
					pass

	@Cog.listener()
	async def on_message_edit(self, before, after):

		log_channel_id = await self.get_log_channel(after.guild.id)

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

				if log_channel_id != False:
					try:
						log_channel = await self.client.fetch_channel(log_channel_id)
						await log_channel.send(embed=embed)
					except:
						pass

	@Cog.listener()
	async def on_message_delete(self, message):

		log_channel_id = await self.get_log_channel(message.guild.id)

		if not message.author.bot:
			embed = Embed(title="Message deletion",
						  description=f"Action by {message.author.display_name}.",
						  colour=message.author.colour,
						  timestamp=datetime.utcnow())

			fields = [("Content", message.content, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			if log_channel_id != False:
				try:
					log_channel = await self.client.fetch_channel(log_channel_id)
					await log_channel.send(embed=embed)
				except:
					pass

def setup(client):
	client.add_cog(Log(client))

