import discord
import os
import requests
import asyncio
from chart_utils import generate_line_chart
from discord.ext import commands
from dotenv import load_dotenv
from difflib import get_close_matches

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("ODDS_API_KEY")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def decimal_to_american(decimal_odds):
    try:
        decimal_odds = float(decimal_odds)
        if decimal_odds >= 2:
            return f"+{int((decimal_odds - 1) * 100)}"
        else:
            return f"-{int(100 / (decimal_odds - 1))}"
    except:
        return "N/A"

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command(name="check")
async def check(ctx, *, team: str):
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'us,uk,eu',
        'markets': 'h2h,spreads',
        'oddsFormat': 'decimal'
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if not isinstance(data, list):
            await ctx.send("❌ API did not return a valid list of games.")
            return

        team_lower = team.lower()
        matched_team = None
        matched_game = None

        for game in data:
            team_names = [game.get("home_team", ""), game.get("away_team", "")]
            for name in team_names:
                if team_lower in name.lower():
                    matched_team = name
                    matched_game = game
                    break
            if matched_team:
                break

        if not matched_team or not matched_game:
            await ctx.send(f"⚠️ No game found matching **{team}**")
            return

        # Pull moneyline and spreads for matched team
        dk_price = None
        pin_price = None
        bo_price = None
        spreads = []

        home = matched_game.get("home_team")
        away = matched_game.get("away_team")

        for bookmaker in matched_game.get("bookmakers", []):
            book = bookmaker["title"].lower()
            for market in bookmaker.get("markets", []):
                if market["key"] == "h2h":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == matched_team:
                            if book == "draftkings":
                                dk_price = outcome["price"]
                            elif book == "pinnacle":
                                pin_price = outcome["price"]
                            elif book == "betonline":
                                bo_price = outcome["price"]
                elif market["key"] == "spreads":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == matched_team:
                            spreads.append(f"{book.capitalize()} | {outcome['name']} {outcome.get('point', 'N/A')} → {decimal_to_american(outcome['price'])}")

        header = f"📊 **{away} vs {home}**"
        dk_val = decimal_to_american(dk_price) if dk_price else "N/A"
        pin_val = decimal_to_american(pin_price) if pin_price else "N/A"
        bo_val = decimal_to_american(bo_price) if bo_price else "N/A"
        spread_text = "\n".join(spreads) if spreads else "No spread data available"

        if dk_price and pin_price and bo_price:
            diff = abs(float(dk_price) - float(pin_price))
            chart_path = generate_line_chart(matched_team, dk_val, pin_val, bo_val)
            await ctx.send(
                f"{header}\n"
                f"Moneyline for {matched_team}: DraftKings: {dk_val} | Pinnacle: {pin_val} | BetOnline: {bo_val} | Δ (DK vs PIN): {diff:.2f}\n"
                f"**Spread Lines:**\n{spread_text}",
                file=discord.File(chart_path)
            )
        else:
            await ctx.send(
                f"{header}\n"
                f"Moneyline for {matched_team}: DraftKings: {dk_val} | Pinnacle: {pin_val} | BetOnline: {bo_val} | Δ: N/A\n"
                f"**Spread Lines:**\n{spread_text}"
            )

    except Exception as e:
        await ctx.send(f"❌ Exception occurred in check: {e}")

bot.run(TOKEN)
