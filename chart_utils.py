import matplotlib.pyplot as plt
from datetime import datetime
import random

def generate_line_chart(team, dk_val, pin_val):
    path = f"/tmp/{team.replace(' ', '_')}_line_chart.png"

    # Simulate historical timestamps and odds for demo purposes
    timestamps = [datetime.now().strftime("%H:%M")]
    dk_odds = [int(dk_val)] if dk_val.startswith(("-", "+")) else [0]
    pin_odds = [int(pin_val)] if pin_val.startswith(("-", "+")) else [0]

    # For visual demo, create a few previous timestamps
    for i in range(4):
        timestamps.insert(0, (datetime.now().replace(minute=(datetime.now().minute - (i+1)*5) % 60)).strftime("%H:%M"))
        dk_odds.insert(0, dk_odds[-1] + random.randint(-5, 5))
        pin_odds.insert(0, pin_odds[-1] + random.randint(-5, 5))

    plt.figure(figsize=(6, 4))
    plt.plot(timestamps, dk_odds, marker='o', label='DraftKings')
    plt.plot(timestamps, pin_odds, marker='o', label='Pinnacle')
    plt.title(f"{team} Line Movement")
    plt.xlabel("Time")
    plt.ylabel("Odds (American)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    return path
