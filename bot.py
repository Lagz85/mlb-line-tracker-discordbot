import discord
import os
import requests
import asyncio
from chart_utils import generate_line_chart
from discord.ext import tasks, commands
from dotenv import load_dotenv

load_dotenv()

def decimal_to_american(decimal_odds):
    if decimal_odds >= 2:
        return f"+{int((decimal_odds - 1) * 100)}"
    else:
        return f"-{int(100 / (decimal_odds - 1))}"

TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("ODDS_API_KEY")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command(name="check")
async def check(ctx, *, team: str):
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'h2h',
        'oddsFormat': 'decimal'
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
            best_match = next((t for t in outcome_teams if team_lower in t.lower()), None)

            if best_match:
                dk_decimal = all_outcomes.get(f"draftkings_{best_match}")
                pin_decimal = all_outcomes.get(f"pinnacle_{best_match}")
                dk = decimal_to_american(dk_decimal) if dk_decimal else "N/A"
                pin = decimal_to_american(pin_decimal) if pin_decimal else "N/A"

                if dk_decimal and pin_decimal:
                    chart_path = generate_line_chart(best_match, dk, pin)
                    await ctx.send(
                        f"📊 **Line Check for {best_match}**\n"
                        f"DraftKings: {dk} | Pinnacle: {pin} | Δ: {abs(float(dk_decimal) - float(pin_decimal)):.2f}",
                        file=discord.File(chart_path)
                    )
                else:
                    await ctx.send(
                        f"📊 **Line Check for {best_match}**\n"
                        f"DraftKings: {dk} | Pinnacle: {pin} | Δ: N/A"
                    )
                return

        await ctx.send(f"⚠️ Could not find odds for **{team}**.")
    except Exception as e:
        await ctx.send(f"❌ Error fetching odds: {e}")

bot.run(TOKEN)
