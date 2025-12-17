import rasterio
import geopandas as gpd
import pandas as pd
from rasterstats import zonal_stats
import numpy as np

df_old = pd.read_csv("ndvi_mndwi_moyennes_echantillon.csv")
df_old["date"] = pd.to_datetime(df_old["date"])

# --- Fichiers sources ---
path_ndvi = "NDVI_2024_test.tif"
path_mndwi = "MNDWI_2024_test.tif"
path_shp = "../mini_etangs.shp"

# --- Charger les étangs ---
etangs = gpd.read_file(path_shp)
id_field = "id"  #nom du champ identifiant
etangs = etangs.set_index(id_field)

# --- Charger les rasters ---
with rasterio.open(path_ndvi) as src_ndvi:
    ndvi = src_ndvi.read()
    ndvi_dates = pd.to_datetime(src_ndvi.descriptions)
    ndvi_meta = src_ndvi.meta
with rasterio.open(path_mndwi) as src_mndwi:
    mndwi = src_mndwi.read()
    mndwi_meta = src_mndwi.meta

n_dates = ndvi.shape[0]
assert ndvi.shape == mndwi.shape, "Les deux rasters doivent avoir les mêmes dimensions."

# --- Calculer les moyennes par étang pour chaque date ---
records = []

for i in range(n_dates):
    print(f"Calcul bande {i+1}/{n_dates} ({ndvi_dates[i].strftime('%Y-%m-%d')})...")

    # Sauvegarder temporairement les bandes (nécessaire pour zonal_stats)
    with rasterio.open("../temp_ndvi.tif", "w", **ndvi_meta) as dst:
        dst.write(ndvi[i], 1)
    with rasterio.open("../temp_mndwi.tif", "w", **mndwi_meta) as dst:
        dst.write(mndwi[i], 1)

    # Moyenne NDVI
    zs_ndvi = zonal_stats(
        etangs, "../temp_ndvi.tif",
        stats="mean", nodata=np.nan, geojson_out=False
    )
    # Moyenne MNDWI
    zs_mndwi = zonal_stats(
        etangs, "../temp_mndwi.tif",
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

# Transformer en DataFrame
df_new = pd.DataFrame(records)

df_all = pd.concat([df_old, df_new], ignore_index=True)

df_all = df_all.drop_duplicates(subset=["pond_id", "date"])

df_all.to_csv("ndvi_mndwi_moyennes_echantillon.csv", index=False)