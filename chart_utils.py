import matplotlib.pyplot as plt
import datetime
import os

def generate_line_chart(team, dk, pin, bo=None):
    # Simulated timestamps and odds
    times = [
        datetime.datetime.now() - datetime.timedelta(hours=2),
        datetime.datetime.now() - datetime.timedelta(hours=1),
        datetime.datetime.now()
    ]
    dk_odds = [int(dk.replace('+','').replace('-',''))] * 3
    pin_odds = [int(pin.replace('+','').replace('-',''))] * 3

    if dk.startswith('-'):
        dk_odds = [-abs(val) for val in dk_odds]
    if pin.startswith('-'):
        pin_odds = [-abs(val) for val in pin_odds]

    plt.figure(figsize=(8, 4))
    plt.plot(times, dk_odds, label='DraftKings', marker='o')
    plt.plot(times, pin_odds, label='Pinnacle', marker='x')

    if bo:
        bo_odds = [int(bo.replace('+','').replace('-',''))] * 3
        if bo.startswith('-'):
            bo_odds = [-abs(val) for val in bo_odds]
        plt.plot(times, bo_odds, label='BetOnline', marker='s')

    plt.xlabel('Time')
    plt.ylabel('Odds (American)')
    plt.title(f'Line Movement - {team}')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    chart_path = "/tmp/chart.png"
    plt.savefig(chart_path)
    plt.close()
    return chart_path
