import discord
import os
import requests
import asyncio
from chart_utils import generate_line_chart
from discord.ext import commands
from dotenv import load_dotenv
from difflib import get_close_matches

load_dotenv()

def decimal_to_american(decimal_odds):
    try:
        decimal_odds = float(decimal_odds)
        if decimal_odds >= 2:
            return f"+{int((decimal_odds - 1) * 100)}"
        else:
            return f"-{int(100 / (decimal_odds - 1))}"
    except:
        return "N/A"

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

        if not isinstance(data, list):
            await ctx.send("❌ API did not return a valid list of games.")
            return

        all_outcomes = {}
        for game in data:
            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] in ['draftkings', 'pinnacle']:
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market.get('outcomes', []):
                                name = outcome['name']
                                price = outcome['price']
                                key = f"{bookmaker['key']}__{name}"
                                all_outcomes[key] = price

        # Match team with fuzzy logic
        team_names = list({key.split("__")[1] for key in all_outcomes})
        match = get_close_matches(team, team_names, n=1, cutoff=0.5)
        if not match:
            await ctx.send(f"⚠️ No close match found for **{team}**")
            return
        matched_team = match[0]

        dk_decimal = all_outcomes.get(f"draftkings__{matched_team}")
        pin_decimal = all_outcomes.get(f"pinnacle__{matched_team}")

        dk_val = decimal_to_american(dk_decimal) if dk_decimal else "N/A"
        pin_val = decimal_to_american(pin_decimal) if pin_decimal else "N/A"

        if dk_decimal and pin_decimal:
            diff = abs(float(dk_decimal) - float(pin_decimal))
            chart_path = generate_line_chart(matched_team, dk_val, pin_val)
            await ctx.send(
                f"📊 **Line Check for {matched_team}**\n"
                f"DraftKings: {dk_val} | Pinnacle: {pin_val} | Δ (decimal): {diff:.2f}",
                file=discord.File(chart_path)
            )
        else:
            await ctx.send(
                f"📊 **Line Check for {matched_team}**\n"
                f"DraftKings: {dk_val} | Pinnacle: {pin_val} | Δ: N/A"
            )

    except Exception as e:
        await ctx.send(f"❌ Exception occurred in check: {e}")

@bot.command(name="testvalue")
async def testvalue(ctx):
    team = "Test Team"
    dk = -120
    pin = +100
    chart_path = generate_line_chart(team, dk, pin)
    await ctx.send(
        f"📊 **(TEST) Value Spot Found:** {team}\n"
        f"DraftKings: {dk} | Pinnacle: {pin} | Δ: {abs(dk - pin)}¢",
        file=discord.File(chart_path)
    )

@bot.command(name="debuglookup")
async def debuglookup(ctx, *, team: str):
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

        if not isinstance(data, list):
            await ctx.send("❌ API did not return a valid list of games.")
            return

        all_outcomes = {}
        for game in data:
            for bookmaker in game.get("bookmakers", []):
                if bookmaker["key"] in ["draftkings", "pinnacle"]:
                    for market in bookmaker.get("markets", []):
                        if market["key"] == "h2h":
                            for outcome in market.get("outcomes", []):
                                name = outcome["name"]
                                price = outcome["price"]
                                key = f"{bookmaker['title']}__{name}"
                                all_outcomes[key] = price

        # Build list of all outcome team names
        team_names = list({key.split("__")[1] for key in all_outcomes})
        match = get_close_matches(team, team_names, n=1, cutoff=0.5)
        if not match:
            await ctx.send(f"⚠️ No close match found for **{team}**")
            return
        matched_team = match[0]

        results = []
        seen_books = set()
        for key, price in all_outcomes.items():
            book, outcome_name = key.split("__")
            if outcome_name == matched_team and book not in seen_books:
                seen_books.add(book)
                converted = decimal_to_american(price)
                results.append(f"{book} (decimal): {price} → American: {converted}")

        if results:
            header = f"🔍 Decimal Odds Debug for '{matched_team}'"
            await ctx.send(header + "\n" + "\n".join(results))
        else:
            await ctx.send(f"⚠️ No odds found for **{matched_team}** in decimal format.")

    except Exception as e:
        await ctx.send(f"❌ Exception occurred: {e}")

bot.run(TOKEN)
