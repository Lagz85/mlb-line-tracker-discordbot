import matplotlib.pyplot as plt

def generate_line_chart(team, dk_odds, pin_odds):
    fig, ax = plt.subplots()
    ax.plot(["DraftKings", "Pinnacle"], [dk_odds, pin_odds], marker='o')
    ax.set_title(f"Line Comparison: {team}")
    ax.set_ylabel("Odds")
    path = f"/tmp/{team}_line_chart.png"
    plt.savefig(path)
    plt.close()
    return path
