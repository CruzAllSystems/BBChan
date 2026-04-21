import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== BB Personality Lines =====
BB_LINES = [
    "BB is here to stay~",
    "Thanks to all your love and support, my lovely senpais~",
    "Ara ara~ Are you behaving yourselves, senpais?",
    "BB-chan is watching you~ Always~"
]


# ===== On Ready =====
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online!")
    bb_idle_messages.start()

# ===== Idle BB Messages =====
@tasks.loop(minutes=120)
async def bb_idle_messages():
    for guild in bot.guilds:
        chan = discord.utils.get(guild.text_channels, name="general")
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages and chan:
                message = random.choice(BB_LINES)
                await channel.send(message)
                break

# ===== POLL COMMAND =====
poll_messages = {}

@bot.tree.command(name="poll", description="Creates a poll in a specific channel")
@app_commands.describe(
    channel="Channel to send the poll to",
    question="Poll question",
    option1="Option 1",
    option2="Option 2"
)
async def poll(interaction: discord.Interaction, channel: discord.TextChannel, question: str, option1: str, option2: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "Ara~ You don't have permission for that, senpai~",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="📊 Poll",
        description=question,
        color=discord.Color.purple()
    )
    embed.add_field(name="1️⃣", value=option1, inline=False)
    embed.add_field(name="2️⃣", value=option2, inline=False)
    msg = await channel.send(embed=embed)

    emojis = ["1️⃣", "2️⃣"]

    for emoji in emojis:
        await msg.add_reaction(emoji)
    poll_messages[msg.id] = emojis

    # Confirm to admin
    await interaction.response.send_message(
        f"Poll deployed to {channel.mention}~",
        ephemeral=True
    )

@bot.event
async def on_raw_reaction_add(payload, counter = [0]):
    if payload.message_id not in poll_messages:
        return

    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    member = guild.get_member(payload.user_id)

    # Loop through all reactions
    for reaction in message.reactions:
        async for user in reaction.users():
            if user.id == payload.user_id and str(reaction.emoji) != str(payload.emoji):
                await message.remove_reaction(reaction.emoji, user)
                counter[0] += 1
                if(counter[0] == 1):
                    await channel.send("Ara~ Trying to vote twice, senpais? How naughty~")
                elif(counter[0] >= 30):
                    await channel.send("If my senpais keep being naughty, I'm going to have to tell on you.~")

# ===== TEMP CHANNEL COMMAND =====
@bot.tree.command(name="temp_channel", description="Create a temporary channel")
@app_commands.describe(name="Channel name", duration="Duration in hours")
async def temp_channel(interaction: discord.Interaction, name: str, duration: int):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("Ara~ You don't have permission, senpai~", ephemeral=True)
        return

    channel = await interaction.guild.create_text_channel(name)
    await interaction.response.send_message(f"Channel {channel.mention} created! It will disappear soon~")

    await asyncio.sleep(duration * 3600)
    await channel.delete()

# ===== ADMIN CONTROLLED MESSAGE =====
@bot.tree.command(name="bb_say", description="Make BB send a message in a specific channel")
@app_commands.describe(
    channel="Channel to send the message to",
    message="Message for BB to say"
)
async def bb_say(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "Ehh~ You can't order BB around like that~",
            ephemeral=True
        )
        return

    formatted = f"{message}~"
    await channel.send(formatted)

    await interaction.response.send_message(
        f"Message delivered to {channel.mention}, senpai~",
        ephemeral=True
    )

# ===== RUN BOT =====
bot.run(TOKEN)