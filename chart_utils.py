import matplotlib.pyplot as plt
import os

def generate_line_chart(team, dk_odds, pin_odds):
    fig, ax = plt.subplots()
    ax.plot(["DraftKings", "Pinnacle"], [dk_odds, pin_odds], marker="o")
    ax.set_title(f"{team} Line Movement")
    ax.set_ylabel("Odds (American)")
    ax.grid(True)
    filename = f"{team.replace(' ', '_')}_odds_chart.png"
    filepath = os.path.join("/tmp", filename)
    plt.savefig(filepath)
    plt.close(fig)
    return filepath
