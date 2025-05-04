import pytz
from datetime import datetime
import discord
import os
import requests
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
        'regions': 'us,us2,uk,eu',
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

        dk_price = None
        pin_price = None
        spreads = []

        start_time_utc = matched_game.get("commence_time")
        game_dt = datetime.fromisoformat(start_time_utc.replace("Z", "+00:00"))
        game_dt_phoenix = game_dt.astimezone(pytz.timezone("America/Phoenix"))
        game_time_str = game_dt_phoenix.strftime("%A, %B %d at %I:%M %p")

        home = matched_game.get("home_team")
        away = matched_game.get("away_team")

        for bookmaker in [b for b in matched_game.get("bookmakers", []) if "draftkings" in b["title"].lower() or "pinnacle" in b["title"].lower()]:
            book = bookmaker["title"].lower()
            for market in bookmaker.get("markets", []):
                if market["key"] == "h2h":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == matched_team:
                            if book == "draftkings":
                                dk_price = outcome["price"]
                            elif book == "pinnacle":
                                pin_price = outcome["price"]
                elif market["key"] == "spreads":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == matched_team:
                            spreads.append(f"{book.capitalize()} | {outcome['name']} {outcome.get('point', 'N/A')} → {decimal_to_american(outcome['price'])}")

        header = f"📊 **{away} vs {home}** — {game_time_str} MST"
        dk_val = decimal_to_american(dk_price) if dk_price else "N/A"
        pin_val = decimal_to_american(pin_price) if pin_price else "N/A"
        spread_text = "\n".join(spreads) if spreads else "No spread data available"

        if dk_price and pin_price:
            diff = abs(float(dk_price) - float(pin_price))
            chart_path = generate_line_chart(matched_team, dk_val, pin_val)
            await ctx.send(
                f"{header}\n"
                f"Moneyline for {matched_team}: DraftKings: {dk_val} | Pinnacle: {pin_val} | Δ: {diff:.2f}\n"
                f"**Spread Lines:**\n{spread_text}",
                file=discord.File(chart_path)
            )
        else:
            await ctx.send(
                f"{header}\n"
                f"Moneyline for {matched_team}: DraftKings: {dk_val} | Pinnacle: {pin_val} | Δ: N/A\n"
                f"**Spread Lines:**\n{spread_text}"
            )

    except Exception as e:
        await ctx.send(f"❌ Exception occurred in check: {e}")

bot.run(TOKEN)

from discord.ext import tasks

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    check_value_spots.start()

@tasks.loop(minutes=5)
async def check_value_spots():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)

    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'us,us2,uk,eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        for game in data:
            home = game.get("home_team")
            away = game.get("away_team")
            game_time = datetime.fromisoformat(game.get("commence_time").replace("Z", "+00:00"))
            game_time_mst = game_time.astimezone(pytz.timezone("America/Phoenix")).strftime("%b %d at %I:%M %p")

            dk_price_home = dk_price_away = pin_price_home = pin_price_away = None

            for bookmaker in game.get("bookmakers", []):
                book = bookmaker["title"].lower()
                if "draftkings" in book or "pinnacle" in book:
                    for market in bookmaker.get("markets", []):
                        if market["key"] == "h2h":
                            for outcome in market["outcomes"]:
                                if "draftkings" in book:
                                    if outcome["name"] == home:
                                        dk_price_home = outcome["price"]
                                    elif outcome["name"] == away:
                                        dk_price_away = outcome["price"]
                                elif "pinnacle" in book:
                                    if outcome["name"] == home:
                                        pin_price_home = outcome["price"]
                                    elif outcome["name"] == away:
                                        pin_price_away = outcome["price"]

            for team in [home, away]:
                try:
                    dk = dk_price_home if team == home else dk_price_away
                    pin = pin_price_home if team == home else pin_price_away
                    if dk and pin:
                        bet_type = "Moneyline"
                        diff = abs(float(pin) - float(dk))
                        if diff >= 0.15 and float(pin) > float(dk):
        f"📈 Pinnacle: {decimal_to_american(pin)}\n"
        f"🕒 Game Time: {game_time_mst}\n"
        f"📊 Line Difference: {diff:.2f}"
    )}\n"
                                f"📈 Pinnacle: {decimal_to_american(pin)}\n"
                                f"🕒 Game Time: {game_time_mst}\n"
                                f"📊 Line Difference: {diff:.2f}"
                            )}\n"
                                f"📈 Pinnacle: {decimal_to_american(pin)}\n"
                                f"🕒 Game Time: {game_time_mst}\n"
                                f"📊 Line Difference: {diff:.2f}"
                            )}\n"
                                f"📈 Pinnacle: {decimal_to_american(pin)}\n"
                                f"🕒 Game Time: {game_time_mst}\n"
                                f"📊 Line Difference: {diff:.2f}"
                            )
                except:
                    continue

    except Exception as e:
        print(f"Value check error: {e}")
        await channel.send(
            f"🚨 VALUE ALERT\n"
            f"Team: {team}\n"
            f"Bet Type: {bet_type}\n"
            f"📉 DraftKings: {decimal_to_american(dk)}\n"
            f"📈 Pinnacle: {decimal_to_american(pin)}\n"
            f"🕒 Game Time: {game_time_mst}\n"
            f"📊 Line Difference: {diff:.2f}"
        )
