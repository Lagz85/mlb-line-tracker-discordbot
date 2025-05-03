def generate_line_chart(team, dk_val, pin_val):
    import matplotlib.pyplot as plt
    import os
    path = f"/tmp/{team.replace(' ', '_')}_chart.png"
    plt.figure()
    plt.title(f"{team} Line Movement")
    plt.plot(["DraftKings", "Pinnacle"], [float(dk_val.strip('+').strip('-')), float(pin_val.strip('+').strip('-'))])
    plt.savefig(path)
    return path
