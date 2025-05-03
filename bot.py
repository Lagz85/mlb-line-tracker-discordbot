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
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    fetch_odds.start()

@tasks.loop(minutes=5)
async def fetch_odds():
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
            game_id = game.get('id')
            home = game.get('home_team')
            away = game.get('away_team')
            timestamp = game.get('commence_time')
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

bot.run(TOKEN)
