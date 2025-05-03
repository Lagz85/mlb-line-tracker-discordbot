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
        data_american = requests.get(url, params=params_american).json()
        data_decimal = requests.get(url, params=params_decimal).json()
        team_lower = team.lower()

        all_outcomes = {}

        # Step 1: Start with decimal odds (Pinnacle + DK if present)
        for game in data_decimal:
            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] in ['draftkings', 'pinnacle']:
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                key = f"{bookmaker['key']}_{outcome['name']}"
                                all_outcomes[key] = {
                                    'decimal': outcome['price'],
                                    'american': decimal_to_american(outcome['price'])
                                }

        # Step 2: Overwrite DraftKings odds with native American format (if available)
        for game in data_american:
            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] == 'draftkings':
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                key = f"draftkings_{outcome['name']}"
                                if key in all_outcomes:
                                    all_outcomes[key]['american'] = outcome['price']

        outcome_teams = set(k.split('_', 1)[1] for k in all_outcomes.keys())
        best_match = next((t for t in outcome_teams if team_lower in t.lower()), None)

        if best_match:
            dk_key = f"draftkings_{best_match}"
            pin_key = f"pinnacle_{best_match}"

            dk_odds = all_outcomes.get(dk_key, {})
            pin_odds = all_outcomes.get(pin_key, {})

            dk_val = dk_odds.get('american', 'N/A')
            pin_val = pin_odds.get('american', 'N/A')

            # Optional: decimal difference if both available
            if 'decimal' in dk_odds and 'decimal' in pin_odds:
                diff = abs(dk_odds['decimal'] - pin_odds['decimal'])
                chart_path = generate_line_chart(best_match, dk_val, pin_val)
                await ctx.send(
                    f"📊 **Line Check for {best_match}**\n"
                    f"DraftKings: {dk_val} | Pinnacle: {pin_val} | Δ (decimal): {diff:.2f}",
                    file=discord.File(chart_path)
                )
            else:
                await ctx.send(
                    f"📊 **Line Check for {best_match}**\n"
                    f"DraftKings: {dk_val} | Pinnacle: {pin_val} | Δ: N/A"
                )
        else:
            await ctx.send(f"⚠️ Could not find odds for **{team}**.")

    except Exception as e:
        await ctx.send(f"❌ Error fetching hybrid odds: {e}")

bot.run(TOKEN)
