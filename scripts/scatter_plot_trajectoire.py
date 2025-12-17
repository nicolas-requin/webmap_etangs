import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# --- Charger le CSV ---
df = pd.read_csv("../ndvi_mndwi_moyennes_par_etang.csv")
df["date"] = pd.to_datetime(df["date"])

# --- Échantillonner X étangs au hasard ---
unique_ponds = df["pond_id"].unique()
sample_ponds = np.random.choice(unique_ponds, size=10, replace=False)

df = df[df["pond_id"].isin(sample_ponds)].copy()

print(f" Échantillon de {len(sample_ponds)} étangs sélectionné ({len(df)} lignes au total)")

dates = sorted(df["date"].unique())
ponds = df["pond_id"].unique()

fig, ax = plt.subplots(figsize=(7,7))
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.set_xlabel("NDVI moyen")
ax.set_ylabel("MNDWI moyen")

# Scatter pour les points actuels
scat = ax.scatter([], [], s=30, alpha=0.8)

# Un dictionnaire de lignes pour chaque étang
lines = {pond: ax.plot([], [], lw=1, alpha=0.5)[0] for pond in ponds}

def update(frame):
    d = dates[frame]
    sub = df[df["date"] <= d]  # toutes les dates jusqu’à la frame actuelle
    
    # Points actuels
    current = df[df["date"] == d]
    scat.set_offsets(current[["ndvi_mean", "mndwi_mean"]].values)

    # Mettre à jour la trajectoire de chaque étang
    for pond in ponds:
        traj = sub[sub["pond_id"] == pond]
        lines[pond].set_data(traj["ndvi_mean"], traj["mndwi_mean"])
    
    ax.set_title(f"NDVI vs MNDWI — {d.strftime('%Y-%m-%d')}")
    return [scat, *lines.values()]

ani = FuncAnimation(fig, update, frames=len(dates), interval=600, blit=False)
plt.show()