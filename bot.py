import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
cogs = ["cogs.train"]

load_dotenv()

@bot.event
async def on_ready():
    print("Bot is up")
    try:
        for cog in cogs:
            await bot.load_extension(cog)
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
        await bot.change_presence(status=discord.Status.online)
    except Exception as e:
        print(e)

bot.run(os.getenv("DISCORD_TOKEN"))