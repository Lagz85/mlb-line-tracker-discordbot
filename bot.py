import discord
import os
import requests
import asyncio
from chart_utils import generate_line_chart
from discord.ext import tasks, commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("ODDS_API_KEY")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    fetch_odds.start()

@tasks.loop(minutes=5)
async def fetch_odds():
    await check_value_spots()

async def check_value_spots():
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'h2h',
        'oddsFormat': 'american'
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        channel = bot.get_channel(CHANNEL_ID)

        for game in data:
            home = game.get('home_team')
            away = game.get('away_team')
            lines = {}

            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] in ['draftkings', 'pinnacle']:
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                team = outcome['name']
                                lines[f"{bookmaker['key']}_{team}"] = outcome['price']

            for team in [home, away]:
                dk = lines.get(f"draftkings_{team}")
                pin = lines.get(f"pinnacle_{team}")
                if dk is not None and pin is not None and abs(dk - pin) >= 15:
                    chart_path = generate_line_chart(team, dk, pin)
                    await channel.send(
                        f"📊 **Value Spot Found:** {team}\n"
                        f"DraftKings: {dk} | Pinnacle: {pin} | Δ: {abs(dk - pin)}",
                        file=discord.File(chart_path)
                    )
    except Exception as e:
        print(f"Error fetching odds: {e}")

@bot.command(name="status")
async def status(ctx):
    await ctx.send("✅ Bot is online and watching lines!")

@bot.command(name="value")
async def value(ctx):
    await ctx.send("🔍 Checking for value spots now...")
    await check_value_spots()

@bot.command(name="check")
async def check(ctx, *, team: str):
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'h2h',
        'oddsFormat': 'american'
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        for game in data:
            teams = [game.get('home_team'), game.get('away_team')]
            if team.lower() in (t.lower() for t in teams):
                lines = {}
                for bookmaker in game.get('bookmakers', []):
                    if bookmaker['key'] in ['draftkings', 'pinnacle']:
                        for market in bookmaker.get('markets', []):
                            if market['key'] == 'h2h':
                                for outcome in market['outcomes']:
                                    lines[f"{bookmaker['key']}_{outcome['name']}"] = outcome['price']

                dk = lines.get(f"draftkings_{team}")
                pin = lines.get(f"pinnacle_{team}")
                if dk is not None and pin is not None:
                    chart_path = generate_line_chart(team, dk, pin)
                    await ctx.send(
                        f"📊 **Line Check for {team}**\n"
                        f"DraftKings: {dk} | Pinnacle: {pin} | Δ: {abs(dk - pin)}",
                        file=discord.File(chart_path)
                    )
                    return
        await ctx.send(f"⚠️ Could not find odds for **{team}**.")
    except Exception as e:
        await ctx.send(f"❌ Error fetching odds: {e}")

@bot.command(name="testvalue")
async def testvalue(ctx):
    team = "Yankees"
    dk = -115
    pin = -140
    chart_path = generate_line_chart(team, dk, pin)
    await ctx.send(
        f"📊 **(TEST) Value Spot Found:** {team}\n"
        f"DraftKings: {dk} | Pinnacle: {pin} | Δ: {abs(dk - pin)}",
        file=discord.File(chart_path)
    )

bot.run(TOKEN)
