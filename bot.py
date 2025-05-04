# temp change: full rebuild with clean indentation

import os
import discord
import pytz
import matplotlib.pyplot as plt
from datetime import datetime
from discord.ext import commands, tasks

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@tasks.loop(minutes=15)
async def check_value_spots():
    await bot.wait_until_ready()
    print("👀 check_value_spots loop fired!")
    # Placeholder for line scanning logic

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print("🕓 Starting value scanning loop every 5 minutes")
    try:
        check_value_spots.start()
        print("📡 Value spot scan loop is now active")
    except Exception as e:
        print(f"🔥 Failed to start value scan loop: {e}")

print("🚦 Executing bot.run(...) now")
bot.run(DISCORD_TOKEN)
