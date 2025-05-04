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

        for game in data:
            for bookmaker in game.get("bookmakers", []):
                if bookmaker["title"].lower() in ["draftkings", "pinnacle"]:
                    for market in bookmaker.get("markets", []):
                        for outcome in market.get("outcomes", []):
                            name = outcome["name"]
                            price = outcome["price"]
                            point = outcome.get("point", "N/A")
                            if market["key"] == "h2h":
                                key = f"{bookmaker['title']}__{name}"
                                h2h_outcomes[key] = price
                            elif market["key"] == "spreads":
                                key = f"{bookmaker['title']}__{name}"
                                spread_lines.append((key, point, price))
                            elif market["key"] == "totals":
                                key = f"{bookmaker['title']}__{name}"
                                total_lines.append((key, point, price))

        team_names = list({key.split("__")[1] for key in h2h_outcomes})
        team_lower = team.lower()

        direct_matches = [name for name in team_names if team_lower in name.lower()]
        match = direct_matches[0] if direct_matches else get_close_matches(team, team_names, n=1, cutoff=0.5)
        if not match:
            await ctx.send(f"⚠️ No close match found for **{team}**")
            return
        matched_team = match[0] if isinstance(match, list) else match

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

        spread_filtered = [f"{key.split('__')[0]} | {matched_team} {pt} → {decimal_to_american(p)}"
                           for key, pt, p in spread_lines if key.endswith(f"__{matched_team}")]
        if spread_filtered:
            msg.append("\n**Spread Lines:**")
            msg.extend(spread_filtered)

        total_filtered = [f"{key.split('__')[0]} | {key.split('__')[1]} {pt} → {decimal_to_american(p)}"
                          for key, pt, p in total_lines if key.endswith(f"__Over") or key.endswith(f"__Under")]
        if total_filtered:
            msg.append("\n**Totals (O/U):**")
            msg.extend(total_filtered)

        if not msg:
            await ctx.send(f"⚠️ No odds found for **{matched_team}** in decimal format.")
            return

        # Split into Discord-safe chunks
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

bot.run(TOKEN)
