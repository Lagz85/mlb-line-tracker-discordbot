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

@bot.command(name="debuglookup")
async def debuglookup(ctx, *, team: str):
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'us,uk,eu',
        'markets': 'h2h,spreads,totals',
        'oddsFormat': 'decimal'
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if not isinstance(data, list):
            await ctx.send("❌ API did not return a valid list of games.")
            return

        h2h_outcomes = {}
        spread_lines = []
        total_lines = []

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

        # Gather odds only for the matched game
        for bookmaker in matched_game.get("bookmakers", []):
            if bookmaker["title"].lower() in ["draftkings", "pinnacle"]:
                for market in bookmaker.get("markets", []):
                    for outcome in market.get("outcomes", []):
                        name = outcome["name"]
                        price = outcome["price"]
                        point = outcome.get("point", "N/A")
                        book = bookmaker["title"]
                        if market["key"] == "h2h":
                            h2h_outcomes[f"{book}__{name}"] = price
                        elif market["key"] == "spreads":
                            if name == matched_team:
                                spread_lines.append(f"{book} | {name} {point} → {decimal_to_american(price)}")
                        elif market["key"] == "totals":
                            total_lines.append(f"{book} | {name} {point} → {decimal_to_american(price)}")

        results = []
        seen_books = set()
        for key, price in h2h_outcomes.items():
            book, outcome_name = key.split("__")
            if outcome_name == matched_team and book not in seen_books:
                seen_books.add(book)
                converted = decimal_to_american(price)
                results.append(f"{book} (decimal): {price} → American: {converted}")

        msg = []
        if results:
            msg.append(f"🔍 **Moneyline for '{matched_team}':**")
            msg.extend(results)
        if spread_lines:
            msg.append("\n**Spread Lines:**")
            msg.extend(spread_lines)
        if total_lines:
            msg.append("\n**Totals (O/U):**")
            msg.extend(total_lines)

        if not msg:
            await ctx.send(f"⚠️ No odds found for **{matched_team}** in decimal format.")
            return

        message = ""
        for line in msg:
            if len(message) + len(line) + 1 > 1990:
                await ctx.send(message)
                message = line
            else:
                message += "\n" + line
        if message:
            await ctx.send(message)

    except Exception as e:
        await ctx.send(f"❌ Exception occurred: {e}")

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
        spreads = []

        home = matched_game.get("home_team")
        away = matched_game.get("away_team")

        for bookmaker in matched_game.get("bookmakers", []):
            book = bookmaker["title"]
            for market in bookmaker.get("markets", []):
                if market["key"] == "h2h":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == matched_team:
                            if book.lower() == "draftkings":
                                dk_price = outcome["price"]
                            elif book.lower() == "pinnacle":
                                pin_price = outcome["price"]
                elif market["key"] == "spreads":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == matched_team:
                            spreads.append(f"{book} | {outcome['name']} {outcome.get('point', 'N/A')} → {decimal_to_american(outcome['price'])}")

        header = f"📊 **{away} vs {home}**"

        if dk_price and pin_price:
            diff = abs(float(dk_price) - float(pin_price))
            dk_val = decimal_to_american(dk_price)
            pin_val = decimal_to_american(pin_price)
            chart_path = generate_line_chart(matched_team, dk_val, pin_val)

            spread_text = "\n".join(spreads) if spreads else "No spread data available"
            await ctx.send(
                f"{header}\n"
                f"Moneyline for {matched_team}: DraftKings: {dk_val} | Pinnacle: {pin_val} | Δ (decimal): {diff:.2f}\n"
                f"**Spread Lines:**\n{spread_text}",
                file=discord.File(chart_path)
            )
        else:
            dk_val = decimal_to_american(dk_price) if dk_price else "N/A"
            pin_val = decimal_to_american(pin_price) if pin_price else "N/A"
            spread_text = "\n".join(spreads) if spreads else "No spread data available"
            await ctx.send(
                f"{header}\n"
                f"Moneyline for {matched_team}: DraftKings: {dk_val} | Pinnacle: {pin_val} | Δ: N/A\n"
                f"**Spread Lines:**\n{spread_text}"
            )

    except Exception as e:
        await ctx.send(f"❌ Exception occurred in check: {e}")


bot.run(TOKEN)
