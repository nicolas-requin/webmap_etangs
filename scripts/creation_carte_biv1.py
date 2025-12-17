import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# --- 1. Fichiers sources ---
path_shp = "../mini_etangs.shp"
path_csv = "bivarie_freqEau_NDVI_test.csv"
id_field = "id"  # identifiant commun

# --- 2. Charger les données ---
etangs = gpd.read_file(path_shp)
etangs[id_field] = etangs[id_field].astype(int)
data = pd.read_csv(path_csv)
data["pond_id"] = data["pond_id"].astype(int)

# --- 3. Jointure shapefile + CSV ---
gdf = etangs.merge(data, left_on=id_field, right_on="pond_id")

# --- 4. Classer les valeurs en 3 classes (quantiles ou seuils fixes) ---
gdf["class_ndvi"] = pd.qcut(gdf["ndvi_moyen"], q=3, labels=[0, 1, 2])
gdf["class_eau"]  = pd.qcut(gdf["freq_eau"], q=3, labels=[0, 1, 2])

# --- 5. Palette bivariée (3x3 = 9 combinaisons possibles) ---
# axe X (NDVI) = vert, axe Y (eau) = bleu
colors = [
    "#e8e8e8", "#b5c0da", "#6c83b5",
    "#b8d6be", "#90b2b3", "#567994",
    "#73ae80", "#5a9178", "#2a5a5b"
]
bivar_cmap = np.array(colors).reshape(3,3)

# --- 6. Associer une couleur à chaque combinaison (eau, ndvi) ---
gdf["color"] = [
    bivar_cmap[int(row.class_eau)][int(row.class_ndvi)]
    for _, row in gdf.iterrows()
]

# --- 7. Tracer la carte ---
fig, ax = plt.subplots(figsize=(8, 8))
gdf.plot(color=gdf["color"], ax=ax, edgecolor="none")

ax.set_title("Carte bivariée — Fréquence d'eau (Y) vs NDVI moyen (X)", fontsize=14)
ax.axis("off")

# --- 8. Ajouter la légende bivariée ---
fig2, ax2 = plt.subplots(figsize=(3, 3))
for i in range(3):
    for j in range(3):
        ax2.add_patch(plt.Rectangle((i, j), 1, 1, color=bivar_cmap[j, i]))
ax2.set_xticks([0.5, 1.5, 2.5])
ax2.set_xticklabels(["Faible", "Moyen", "Fort"])
ax2.set_yticks([0.5, 1.5, 2.5])
ax2.set_yticklabels(["Faible", "Moyen", "Fort"])
ax2.set_xlabel("NDVI moyen")
ax2.set_ylabel("Fréquence d’eau")
ax2.set_xlim(0, 3)
ax2.set_ylim(0, 3)
ax2.set_title("Légende bivariée", fontsize=12)
plt.tight_layout()

plt.show()
