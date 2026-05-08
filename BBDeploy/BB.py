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
    #bb_idle_messages.start()

# ===== Idle BB Messages =====
@tasks.loop(minutes=720)
async def bb_idle_messages():
    for guild in bot.guilds:
        chan = discord.utils.get(guild.text_channels, name="general")
        if chan.permissions_for(guild.me).send_messages:
            message = random.choice(BB_LINES)
            await chan.send(message)
            break

#=====COMMANDS TO SHUT OFF AND TURN ON BB IDLE MESSAGES======
@bot.tree.command(name="bb_talk", description="Activate BB's auto/idle messages in general")
async def bb_talk(interaction: discord.Interaction):
    if not bb_idle_messages.is_running():
        bb_idle_messages.start()

    await interaction.response.send_message(
        f"BB will now speak cutesy every so often hehe.~",
        ephemeral=True
    )

@bot.tree.command(name="bb_shutup", description="Deactivates BB's auto/idle messages in the text channels")
async def bb_shutup(interaction: discord.Interaction):
    bb_idle_messages.stop()

    await interaction.response.send_message(
        "Ara~ silencing me already, senpai?",
        ephemeral=True
    )

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
    global messagekey
    messagekey = msg.id # key to keep track of poll imbeds
    poll_messages[messagekey] = emojis

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
            if (user.id == payload.user_id and str(reaction.emoji) != str(payload.emoji)) or (user.id == payload.user_id and reaction.emoji not in poll_messages[messagekey]):
                await message.remove_reaction(reaction.emoji, user)
                counter[0] += 1
                if(counter[0] == 1):
                    await channel.send("Ara~ Trying to alter votes senpais? How naughty~")


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
async def bb_say(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "Ehh~ You can't order BB around like that~",
            ephemeral=True
        )
        return

    formatted = f"{message}"
    await channel.send(formatted)

    await interaction.response.send_message(
        f"Message delivered to {channel.mention}, senpai~",
        ephemeral=True
    )

# ===== ADMIN CONTROLLED IMAGE SEND=====
@bot.tree.command(name="bb_image", description="Make BB send an image")
@app_commands.describe(
    channel="Channel to send the image to",
    image="Image file to upload",
    caption="Optional caption"
)
async def bb_image(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    image: discord.Attachment,
    caption: str = None
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "Ehh~ You can't command BB like that, senpai~",
            ephemeral=True
        )
        return

    if not channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message(
            "BB can't speak there~ how tragic~",
            ephemeral=True
        )
        return

    #Basic type check
    if not image.content_type or not image.content_type.startswith("image"):
        await interaction.response.send_message(
            "That doesn't look like an image, senpai~",
            ephemeral=True
        )
        return

    file = await image.to_file()
    await channel.send(content=(caption + "~" if caption else None), file=file)

    await interaction.response.send_message(
        f"Image delivered to {channel.mention}~",
        ephemeral=True
    )

# ======== BB ROLLING DICE ========
@bot.tree.command(name="bb_roll", description="Have BB roll a d20 in a selected channel")
@app_commands.describe(channel="The channel BB should send the roll to")
async def bb_roll(interaction: discord.Interaction, channel: discord.TextChannel):

    # Admin check
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "Ara~ only admins can make BB roll dice publicly, senpai~",
            ephemeral=True
        )
        return

    # Roll the dice
    roll = random.randint(1, 20)

    # BB flavor text
    if roll == 20:
        result_text = (
            f"🎲 **Natural 20!!**\n"
            f"Ufufu~ BB delivers perfection once again, senpai~"
        )

    elif roll == 1:
        result_text = (
            f"🎲 **Natural 1...**\n"
            f"Oh dear~ what an unfortunate little disaster, senpai~"
        )

    else:
        result_text = (
            f"🎲 BB rolled a **{roll}**!\n"
            f"How exciting~"
        )

    # Send to target channel
    await channel.send(result_text)

    # Respond privately to command user
    await interaction.response.send_message(
        f"BB rolled the dice in {channel.mention}~",
        ephemeral=True
    )

# ===== RUN BOT =====
bot.run(TOKEN)