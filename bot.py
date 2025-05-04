# temp change: replaced if/elif with two separate if statements

import os
import discord
import pytz
import matplotlib.pyplot as plt
from datetime import datetime
from discord.ext import commands, tasks

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@tasks.loop(minutes=15)
async def check_value_spots():
    await bot.wait_until_ready()
    print("👀 check_value_spots loop fired!")
    import requests
    from pytz import timezone
    PHX = timezone('America/Phoenix')
    try:
        url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
        params = {
            'apiKey': os.getenv('ODDS_API_KEY'),
            'regions': 'us',
            'markets': 'h2h',
            'oddsFormat': 'american'
        }
        response = requests.get(url, params=params)
        games = response.json()
        for game in games:
            dk_odds = None
            pin_odds = None
            start_time_utc = game.get("commence_time")
            start_time_local = datetime.fromisoformat(start_time_utc.replace("Z", "+00:00")).astimezone(PHX)
            game_time_str = start_time_local.strftime("%b %d at %I:%M %p")
            for bookmaker in game.get("bookmakers", []):
                if bookmaker['key'] == 'draftkings':
                    dk_odds = bookmaker['markets'][0]['outcomes']
                if bookmaker['key'] == 'pinnacle':
                    pin_odds = bookmaker['markets'][0]['outcomes']
                    dk_odds = bookmaker['markets'][0]['outcomes']
                    dk_odds = bookmaker['markets'][0]['outcomes']
                dk_odds = bookmaker['markets'][0]['outcomes']
                    pin_odds = bookmaker['markets'][0]['outcomes']
                    pin_odds = bookmaker['markets'][0]['outcomes']
                pin_odds = bookmaker['markets'][0]['outcomes']
            if not dk_odds or not pin_odds:
                continue
            try:
                for team in ['home_team', 'away_team']:
                    team_name = game[team]
                    dk_line = next((o['price'] for o in dk_odds if o['name'] == team_name), None)
                    pin_line = next((o['price'] for o in pin_odds if o['name'] == team_name), None)
                    if dk_line is not None and pin_line is not None:
                        diff = abs(pin_line - dk_line)
                        if diff >= 15:
                            message = (
                                f"🚨 VALUE ALERT\n"
                                f"Team: {team_name}\n"
                                f"Bet Type: Moneyline\n"
                                f"📉 DraftKings: {dk_line}\n"
                                f"📈 Pinnacle: {pin_line}\n"
                                f"🕒 Game Time: {game_time_str}\n"
                                f"📊 Line Difference: {round(diff / 100, 2)}"
                            )
                            channel = bot.get_channel(int(os.getenv("ALERT_CHANNEL_ID")))
                            await channel.send(message)
            except Exception as alert_error:
                print(f"⚠️ Alert parsing error: {alert_error}")
    except Exception as e:
        print(f"🔥 Error during value scan: {e}")
    await bot.wait_until_ready()
    print("👀 check_value_spots loop fired!")
    # Placeholder for line scanning logic

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print("🕓 Starting value scanning loop every 5 minutes")
    try:
        check_value_spots.start()
        await check_value_spots()
        print("📡 Value spot scan loop is now active")
    except Exception as e:
        print(f"🔥 Failed to start value scan loop: {e}")

print("🚦 Executing bot.run(...) now")
bot.run(DISCORD_TOKEN)
