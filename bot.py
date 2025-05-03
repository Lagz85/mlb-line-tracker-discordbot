import discord
import os
import requests
import asyncio
from chart_utils import generate_line_chart
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("ODDS_API_KEY")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def format_american(odds):
    try:
        val = int(odds)
        return f"+{val}" if val > 0 else str(val)
    except:
        return odds

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
        data = requests.get(url, params=params).json()
        team_lower = team.lower()
        all_outcomes = {}

        for game in data:
            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] in ['draftkings', 'pinnacle']:
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                key = f"{bookmaker['key']}_{outcome['name']}"
                                all_outcomes[key] = outcome['price']

        outcome_teams = set(k.split('_', 1)[1] for k in all_outcomes.keys())
        best_match = next((t for t in outcome_teams if team_lower in t.lower()), None)

        if best_match:
            dk = all_outcomes.get(f"draftkings_{best_match}", "N/A")
            pin = all_outcomes.get(f"pinnacle_{best_match}", "N/A")
            dk_str = format_american(dk)
            pin_str = format_american(pin)

            if dk != "N/A" and pin != "N/A":
                chart_path = generate_line_chart(best_match, dk_str, pin_str)
                diff = abs(int(dk) - int(pin))
                await ctx.send(
                    f"📊 **Line Check for {best_match}**\n"
                    f"DraftKings: {dk_str} | Pinnacle: {pin_str} | Δ: {diff}¢",
                    file=discord.File(chart_path)
                )
            else:
                await ctx.send(
                    f"📊 **Line Check for {best_match}**\n"
                    f"DraftKings: {dk_str} | Pinnacle: {pin_str} | Δ: N/A"
                )
        else:
            await ctx.send(f"⚠️ Could not find odds for **{team}**.")

    except Exception as e:
        await ctx.send(f"❌ Error fetching American odds: {e}")

@bot.command(name="testvalue")
async def testvalue(ctx):
    team = "Test Team"
    dk = -120
    pin = +100
    chart_path = generate_line_chart(team, dk, pin)
    await ctx.send(
        f"📊 **(TEST) Value Spot Found:** {team}\n"
        f"DraftKings: {format_american(dk)} | Pinnacle: {format_american(pin)} | Δ: {abs(dk - pin)}¢",
        file=discord.File(chart_path)
    )

bot.run(TOKEN)
