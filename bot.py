import discord
import os
import requests
import asyncio
from chart_utils import generate_line_chart
from discord.ext import commands
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
    params_american = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'h2h',
        'oddsFormat': 'american'
    }
    params_decimal = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    }

    try:
        response_american = requests.get(url, params=params_american).json()
        response_decimal = requests.get(url, params=params_decimal).json()
        team_lower = team.lower()

        for game in response_american:
            all_outcomes = {}
            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] == 'draftkings':
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                all_outcomes[f"draftkings_{outcome['name']}"] = outcome['price']

        for game in response_decimal:
            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] == 'pinnacle':
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                all_outcomes[f"pinnacle_{outcome['name']}"] = decimal_to_american(outcome['price'])
                                all_outcomes[f"pinnacle_decimal_{outcome['name']}"] = outcome['price']

        outcome_teams = set(k.split('_', 1)[1] for k in all_outcomes if not k.startswith("pinnacle_decimal_"))
        best_match = next((t for t in outcome_teams if team_lower in t.lower()), None)

        if best_match:
            dk = all_outcomes.get(f"draftkings_{best_match}", "N/A")
            pin = all_outcomes.get(f"pinnacle_{best_match}", "N/A")
            dk_decimal = None
            pin_decimal = all_outcomes.get(f"pinnacle_decimal_{best_match}", None)

            if isinstance(dk, (int, float, str)) and dk != "N/A":
                dk_decimal = None  # not tracking DK decimal in this hybrid

            if dk != "N/A" and pin != "N/A":
                chart_path = generate_line_chart(best_match, dk, pin)
                diff = (
                    abs(float(pin_decimal) - float(int(dk)/-100 + 1)) if "-" in str(dk)
                    else abs(float(pin_decimal) - (int(dk.strip("+"))/100 + 1))
                )
                await ctx.send(
                    f"📊 **Line Check for {best_match}**\n"
                    f"DraftKings: {dk} | Pinnacle: {pin} | Δ (decimal diff): {diff:.2f}",
                    file=discord.File(chart_path)
                )
            else:
                await ctx.send(
                    f"📊 **Line Check for {best_match}**\n"
                    f"DraftKings: {dk} | Pinnacle: {pin} | Δ: N/A"
                )
        else:
            await ctx.send(f"⚠️ Could not find odds for **{team}**.")

    except Exception as e:
        await ctx.send(f"❌ Error fetching hybrid odds: {e}")

bot.run(TOKEN)
