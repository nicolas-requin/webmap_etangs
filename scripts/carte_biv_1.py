"""
Ce code découpe calcule des stats zonales de moyenne sur des couches de NDVI et de masque binaire de présence d'eau
par pixel, sur une année. Pour chaque bande correspondant à une date, les infos sont enregistrées dans un csv
puis la moyenne totale sur l'année est faite.
"""
import rasterio
import geopandas as gpd
import numpy as np
import pandas as pd
from rasterstats import zonal_stats

# --- Fichiers sources ---
path_shp = "../mini_etangs.shp"
path_water = "../binaire_eau_2018_test.tif"   # binaire (0 = pas d'eau, 1 = eau)
path_ndvi = "../NDVI_2018_test.tif"

id_field = "id"  # nom du champ identifiant des étangs

# --- Charger shapefile ---
etangs = gpd.read_file(path_shp)
etangs["id"] = etangs["id"].astype(int)
etangs = etangs.set_index("id")

# --- Ouvrir les rasters ---
with rasterio.open(path_water) as src_w:
    water = src_w.read().astype(float)
    water_meta = src_w.meta
    nodata_water = src_w.nodata if src_w.nodata is not None else -1000
    water[water == nodata_water] = np.nan  # Remplacer nodata par NaN

with rasterio.open(path_ndvi) as src_n:
    ndvi = src_n.read().astype(float)
    ndvi_meta = src_n.meta
    nodata_ndvi = src_n.nodata if src_n.nodata is not None else -1000
    ndvi[ndvi == nodata_ndvi] = np.nan  # Remplacer nodata par NaN
    ndvi_dates = [f"Bande_{i+1}" for i in range(ndvi.shape[0])]

n_dates = water.shape[0]
assert ndvi.shape[0] == n_dates, "Le masque eau et le NDVI doivent avoir le même nombre de bandes"
assert water.shape == ndvi.shape, "Les rasters doivent avoir les mêmes dimensions."

records = []

for i in range(n_dates):
    date_str = ndvi_dates[i]
    print(f"Calcul bande {i+1}/{n_dates} ({date_str})...")

    # Sauvegarde temporaire
    with rasterio.open("temp_water.tif", "w", **water_meta) as dst:
        dst.write(water[i], 1)
    with rasterio.open("temp_ndvi.tif", "w", **ndvi_meta) as dst:
        dst.write(ndvi[i], 1)

    # Calcul zonal
    zs_water = zonal_stats(etangs, "temp_water.tif", stats="mean", nodata=nodata_water, all_touched=True)
    zs_ndvi = zonal_stats(etangs, "temp_ndvi.tif", stats="mean", nodata=nodata_ndvi, all_touched=True)

    # Enregistrer les résultats pour chaque étang
    for pond_id, zw, zn in zip(etangs.index, zs_water, zs_ndvi):
        records.append({
            "pond_id": pond_id,
            "date": date_str,
            "freq_eau": zw["mean"],   # proportion d’eau à cette date
            "ndvi_mean": zn["mean"]   # NDVI moyen à cette date
        })

# --- DataFrame complet (toutes les dates) ---
df = pd.DataFrame(records)
df.to_csv("ndvi_freqEau_test.csv", index=False)
print("Sauvegardé : ndvi_freqEau_test.csv")

# --- Moyenne annuelle par étang ---
annual = df.groupby("pond_id").agg(
    freq_eau=("freq_eau", "mean"),
    ndvi_moyen=("ndvi_mean", "mean")
).reset_index()

annual.to_csv("bivarie_freqEau_NDVI_test.csv", index=False)
print("Sauvegardé : bivarie_freqEau_NDVI_test.csv")