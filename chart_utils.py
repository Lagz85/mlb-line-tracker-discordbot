import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random

def generate_line_chart(team, dk_val, pin_val, bo_val=None):
    path = f"/tmp/{team.replace(' ', '_')}_line_chart.png"

    # Use current time and simulate past 4 intervals
    now = datetime.now()
    timestamps = [(now - timedelta(minutes=i * 5)).strftime("%H:%M") for i in reversed(range(5))]

    def build_line(start_val):
        try:
            base = int(start_val)
        except:
            base = 0
        return [base + random.randint(-5, 5) for _ in range(5)]

    dk_odds = build_line(dk_val)
    pin_odds = build_line(pin_val)
    bo_odds = build_line(bo_val) if bo_val else []

    plt.figure(figsize=(7, 4))
    plt.plot(timestamps, dk_odds, marker='o', label='DraftKings')
    plt.plot(timestamps, pin_odds, marker='o', label='Pinnacle')
    if bo_odds:
        plt.plot(timestamps, bo_odds, marker='o', label='BetOnline')

    plt.title(f"{team} Line Movement (Simulated)")
    plt.xlabel("Time")
    plt.ylabel("Odds (American)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    return path
