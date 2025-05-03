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
                for outcome_team in [k.split('_', 1)[1] for k in lines.keys() if team in k]:
                    dk = lines.get(f"draftkings_{outcome_team}")
                    pin = lines.get(f"pinnacle_{outcome_team}")
                    if dk is not None and pin is not None and abs(dk - pin) >= 15:
                        chart_path = generate_line_chart(outcome_team, dk, pin)
                        await channel.send(
                            f"📊 **Value Spot Found:** {outcome_team}\n"
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
        team_lower = team.lower()

        for game in data:
            all_outcomes = {}
            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] in ['draftkings', 'pinnacle']:
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                name = outcome['name']
                                all_outcomes[f"{bookmaker['key']}_{name}"] = outcome['price']

            outcome_teams = set(k.split('_', 1)[1] for k in all_outcomes.keys())
            match = next((t for t in outcome_teams if team_lower in t.lower()), None)
            if match:
                dk = all_outcomes.get(f"draftkings_{match}")
                pin = all_outcomes.get(f"pinnacle_{match}")
                if dk is not None and pin is not None:
                    chart_path = generate_line_chart(match, dk, pin)
                    await ctx.send(
                        f"📊 **Line Check for {match}**\n"
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

@bot.command(name="listteams")
async def listteams(ctx):
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

        seen = set()
        for game in data:
            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] in ['draftkings', 'pinnacle']:
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                seen.add(outcome['name'])

        sorted_names = sorted(seen)
        message_lines = ["**Available Team Names:**"] + list(sorted_names)
        message = "\n".join(message_lines)

        for i in range(0, len(message), 1900):
            await ctx.send(message[i:i+1900])
    except Exception as e:
        await ctx.send(f"❌ Error fetching team names: {e}")

@bot.command(name="showoutcomes")
async def showoutcomes(ctx, *, team: str):
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
        team_lower = team.lower()

        matches = set()
        for game in data:
            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] in ['draftkings', 'pinnacle']:
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                if team_lower in outcome['name'].lower():
                                    matches.add(outcome['name'])

        if matches:
            msg = "**Matching Outcome Names:**\n" + "\n".join(sorted(matches))
            for i in range(0, len(msg), 1900):
                await ctx.send(msg[i:i+1900])
        else:
            await ctx.send(f"⚠️ No outcome names matched **{team}**.")
    except Exception as e:
        await ctx.send(f"❌ Error fetching outcome names: {e}")

bot.run(TOKEN)

@bot.command(name="showoutcomes")
async def showoutcomes(ctx, *, team: str):
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
        team_lower = team.lower()
        matches = []

        for game in data:
            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] in ['draftkings', 'pinnacle']:
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                name = outcome['name']
                                price = outcome['price']
                                if team_lower in name.lower():
                                    matches.append(f"{bookmaker['key']} - {name}: {price}")

        if matches:
            message = "**Matched Outcome Names:**\n" + "\n".join(matches)
        else:
            message = f"⚠️ No outcomes matched '{team}' in current odds."

        for i in range(0, len(message), 1900):
            await ctx.send(message[i:i+1900])
    except Exception as e:
        await ctx.send(f"❌ Error fetching outcome names: {e}")

