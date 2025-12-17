import rasterio
import geopandas as gpd
import pandas as pd
from rasterstats import zonal_stats
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# --- Fichiers sources ---
path_ndvi = "../NDVI_2018_test.tif"
path_mndwi = "MNDWI_2018_test.tif"
path_shp = "../mini_etangs.shp"

# --- Charger les étangs ---
etangs = gpd.read_file(path_shp)
id_field = "id"  # nom du champ identifiant
etangs = etangs.set_index(id_field)

# --- Charger les rasters ---

with rasterio.open(path_ndvi) as src_ndvi:
    ndvi = src_ndvi.read()
    n_dates = ndvi.shape[0]
    ndvi_dates = pd.date_range(start="2018-01-06", periods=n_dates, freq="10D")
    ndvi_meta = src_ndvi.meta
with rasterio.open(path_mndwi) as src_mndwi:
    mndwi = src_mndwi.read()
    mndwi_meta = src_mndwi.meta

assert ndvi.shape == mndwi.shape, "Les deux rasters doivent avoir les mêmes dimensions."

# --- Calculer les moyennes par étang pour chaque date ---
records = []

for i in range(n_dates):
    print(f"Calcul bande {i+1}/n_dates ({ndvi_dates[i].strftime('%Y-%m-%d')})...")

    # Sauvegarder temporairement les bandes (nécessaire pour zonal_stats)
    with rasterio.open("temp_ndvi.tif", "w", **ndvi_meta) as dst:
        dst.write(ndvi[i], 1)
    with rasterio.open("temp_mndwi.tif", "w", **mndwi_meta) as dst:
        dst.write(mndwi[i], 1)

    # Moyenne NDVI
    zs_ndvi = zonal_stats(
        etangs, "temp_ndvi.tif",
        stats="mean", nodata=np.nan, geojson_out=False
    )
    # Moyenne MNDWI
    zs_mndwi = zonal_stats(
        etangs, "temp_mndwi.tif",
        stats="mean", nodata=np.nan, geojson_out=False
    )

    # Construire la ligne pour chaque étang
    for pond_id, nd, mw in zip(etangs.index, zs_ndvi, zs_mndwi):
        records.append({
            "pond_id": pond_id,
            "date": ndvi_dates[i],
            "ndvi_mean": nd["mean"],
            "mndwi_mean": mw["mean"]
        })


# --- Convertir en DataFrame final ---
df = pd.DataFrame(records)
print(df.head())

df.to_csv("ndvi_mndwi_moyennes_echantillon.csv", index=False)

df = pd.read_csv("ndvi_mndwi_moyennes_echantillon.csv")
df["date"] = pd.to_datetime(df["date"])  # <-- ligne essentielle !

dates = sorted(df["date"].unique())
ponds = df["pond_id"].unique()

fig, ax = plt.subplots(figsize=(6,6))
scat = ax.scatter([], [], s=40, alpha=0.7)
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.set_xlabel("NDVI moyen")
ax.set_ylabel("MNDWI moyen")

def update(frame):
    d = dates[frame]
    sub = df[df["date"] == d]
    scat.set_offsets(sub[["ndvi_mean", "mndwi_mean"]].values)
    ax.set_title(f"NDVI vs MNDWI — {d.strftime('%Y-%m-%d')}")
    return scat,

ani = FuncAnimation(fig, update, frames=len(dates), interval=500, repeat=True)
plt.show()