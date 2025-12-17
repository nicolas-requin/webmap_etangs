"""
scatter_dynamique.py
Animation NDVI / MNDWI colorée selon le comportement hydrique des étangs,
avec filtrage saisonnier et lissage mensuel optionnels.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ---------------------------------------------------------------------
# PARAMÈTRES À AJUSTER
# ---------------------------------------------------------------------
INPUT_CSV = "ndvi_mndwi_moyennes_echantillon.csv"

# Seuils NDVI / MNDWI pour les cadrants
NDVI0 = 0.3
MNDWI0 = 0.3

# Options de traitement
SMOOTHING = True          # True = moyenne par mois
START_DATE = "2023-09-07"           # YYYY-MM-DD
END_DATE = "2024-02-24"             # YYYY-MM-DD

# ---------------------------------------------------------------------
# LECTURE ET PRÉPARATION DES DONNÉES
# ---------------------------------------------------------------------
df = pd.read_csv(INPUT_CSV)
df["date"] = pd.to_datetime(df["date"])

# --- Lissage mensuel (optionnel) ---
if SMOOTHING:
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df = (
        df.groupby(["pond_id", "year", "month"], as_index=False)
          .agg({
              "ndvi_mean": "mean",
              "mndwi_mean": "mean"
          })
    )
    # date fictive au 15 du mois
    df["date"] = pd.to_datetime(df["year"].astype(str) + "-" + df["month"].astype(str) + "-15")
    
# Filtrage temporel
df = df[(df["date"] >= pd.to_datetime(START_DATE)) &
        (df["date"] <= pd.to_datetime(END_DATE))]

print(f"{df['pond_id'].nunique()} étangs chargés, {len(df)} enregistrements initiaux.")

# ---------------------------------------------------------------------
# DÉTERMINATION DES CADRANTS ET DES CHANGEMENTS
# ---------------------------------------------------------------------
def quadrant(ndvi, mndwi, ndvi0=NDVI0, mndwi0=MNDWI0):
    if ndvi >= ndvi0 and mndwi >= mndwi0:
        return "Q1"  # eau + végétalisé
    elif ndvi < ndvi0 and mndwi >= mndwi0:
        return "Q2"  # eau + peu végétalisé
    elif ndvi < ndvi0 and mndwi < mndwi0:
        return "Q3"  # sec + peu végétalisé
    else:
        return "Q4"  # sec + végétalisé

#pour chaque ligne du df, détermination du cadrant et enregistrement de cette donnée dans le tableau
df["quadrant"] = df.apply(lambda r: quadrant(r.ndvi_mean, r.mndwi_mean), axis=1)
#Tri chronologique par étang pour avoir la séquence des cadrants traversés
df = df.sort_values(["pond_id", "date"])
# ordre temporel par étang
df = df.sort_values(["pond_id", "date"])
# cadrant précédent (shift décale les lignes vers le bas pour gérer les premières observ)
df["quadrant_prev"] = df.groupby("pond_id")["quadrant"].shift()
# changement : True seulement si quadrant_prev existe ET quadrant existe ET sont différents
df["change"] = (
    df["quadrant_prev"].notna()          # il y a bien une valeur précédente
    & df["quadrant"].notna()             # la valeur courante n'est pas manquante
    & (df["quadrant"] != df["quadrant_prev"])  # et les deux sont différents
)

# forcer boolean dtype
df["change"] = df["change"].astype(bool)

# ---------------------------------------------------------------------
# CALCUL DU COMPORTEMENT HYDRIQUE GLOBAL
# ---------------------------------------------------------------------
summary = (
    df.groupby("pond_id")
      .agg(
          n_changes=("change", "sum"),
          first_quadrant=("quadrant", "first"),
          last_quadrant=("quadrant", "last")
      )
      .reset_index()
)

conditions = [
    (summary["n_changes"] == 0),
    (summary["n_changes"] > 0) & (summary["first_quadrant"] == summary["last_quadrant"]),
    (summary["n_changes"] > 0) & (summary["first_quadrant"] != summary["last_quadrant"])
]
labels = ["Stable", "Cyclique", "Transition"]
summary["dynamique"] = np.select(conditions, labels, default="Inconnu")

# Fusion avec les données principales
df = df.merge(summary[["pond_id", "dynamique"]], on="pond_id", how="left")

# ---------------------------------------------------------------------
# CALCUL DES MOYENNES PAR TYPE DE DYNAMIQUE ET PAR DATE
# ---------------------------------------------------------------------
group_means = (
    df.groupby(["date", "dynamique"], as_index=False)
      .agg({
          "ndvi_mean": "mean",
          "mndwi_mean": "mean"
      })
)

# ---------------------------------------------------------------------
# STATISTIQUES DES COMPORTEMENTS
# ---------------------------------------------------------------------
counts = summary["dynamique"].value_counts()
print("\n Répartition des étangs selon leur comportement hydrique :")
for k, v in counts.items():
    print(f"  - {k}: {v} étangs")

# ---------------------------------------------------------------------
# ANIMATION SCATTER PLOT
# ---------------------------------------------------------------------
dates = sorted(df["date"].unique())
dynamics_colors = {"Stable": "forestgreen", "Cyclique": "gold", "Transition": "crimson"}

fig, ax = plt.subplots(figsize=(7, 7))
scat = ax.scatter([], [], s=40, alpha=0.8)
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.set_xlabel("NDVI moyen")
ax.set_ylabel("MNDWI moyen")

# --- Tracé des lignes de cadrants ---
ax.axvline(x=NDVI0, color="gray", linestyle="--", lw=1)
ax.axhline(y=MNDWI0, color="gray", linestyle="--", lw=1)
ax.text(NDVI0 + 0.02, MNDWI0 + 0.02, "Q1", color="gray", fontsize=10)
ax.text(NDVI0 - 0.18, MNDWI0 + 0.02, "Q2", color="gray", fontsize=10)
ax.text(NDVI0 - 0.18, MNDWI0 - 0.08, "Q3", color="gray", fontsize=10)
ax.text(NDVI0 + 0.02, MNDWI0 - 0.08, "Q4", color="gray", fontsize=10)

# Légende
for label, color in dynamics_colors.items():
    ax.scatter([], [], c=color, label=label)
ax.legend(title="Comportement", loc="upper left")

# --- Scatter principal ---
scat = ax.scatter([], [], s=40, alpha=0.8, zorder=2)

# --- Centroïdes (points moyens par groupe) ---
mean_scat = ax.scatter([], [], 
                       s=120, marker="X",
                       edgecolor="black", linewidth=1.2,
                       alpha=1.0, zorder=4)

# --- Trajectoires des centroïdes ---
trajectories = {}
for dyn, color in dynamics_colors.items():
    traj = group_means[group_means["dynamique"] == dyn].sort_values("date")
    trajectories[dyn] = {
        "dates": traj["date"].values.astype("datetime64[ns]"),  # 🔹 conversion explicite ici
        "x": traj["ndvi_mean"].values,
        "y": traj["mndwi_mean"].values,
        "line": ax.plot([], [], color=color, lw=2, alpha=0.7, zorder=3)[0],
    }


# --- Fonction d’update ---
def update(frame):
    d = dates[frame]
    sub = df[df["date"] == d]  # sélectionne uniquement les points de cette date
    sub_means = group_means[group_means["date"] == d]

    # points individuels
    scat.set_offsets(sub[["ndvi_mean", "mndwi_mean"]].values)
    scat.set_color(sub["dynamique"].map(dynamics_colors))

    # centroïdes
    mean_coords = sub_means[["ndvi_mean", "mndwi_mean"]].values
    mean_colors = sub_means["dynamique"].map(dynamics_colors)
    mean_scat.set_offsets(mean_coords)
    mean_scat.set_facecolor(mean_colors)

    # trajectoires cumulatives
    for dyn, traj in trajectories.items():
        idx = np.searchsorted(traj["dates"], np.datetime64(d.to_pydatetime()), side="right")
        traj["line"].set_data(traj["x"][:idx], traj["y"][:idx])

    ax.set_title(f"NDVI vs MNDWI — {d.strftime('%Y-%m-%d')}")
    return [scat, mean_scat] + [t["line"] for t in trajectories.values()]

# --- Animation ---
ani = FuncAnimation(fig, update, frames=len(dates), interval=800, blit=True, repeat=True)
plt.tight_layout()
plt.show()
