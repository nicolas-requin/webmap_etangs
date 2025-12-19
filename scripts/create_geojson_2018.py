"""
Calcul de stats zonales NDVI et fréquence d'eau par étang et par date,
export en GeoJSON temporel pour webmapping.
"""

import rasterio
import os
import geopandas as gpd
import numpy as np
import tempfile
from rasterstats import zonal_stats

# --- Fichiers sources ---
path_shp = "layers/mini_etangs.shp"
path_water = "layers/MNDWI_2018_test.tif"
path_ndvi = "layers/NDVI_2018_test.tif"

id_field = "id"

# --- Charger shapefile ---
etangs = gpd.read_file(path_shp)
if etangs.crs is None:
    etangs = etangs.set_crs(epsg=2154)
etangs[id_field] = etangs[id_field].astype(int)
etangs = etangs.set_index(id_field)

# --- Ouvrir les rasters ---
with rasterio.open(path_water) as src_w:
    water = src_w.read().astype(float)
    water_meta = src_w.meta
    nodata_water = src_w.nodata if src_w.nodata is not None else -1000
    water[water == nodata_water] = np.nan

with rasterio.open(path_ndvi) as src_n:
    ndvi = src_n.read().astype(float)
    ndvi_meta = src_n.meta
    nodata_ndvi = src_n.nodata if src_n.nodata is not None else -1000
    ndvi[ndvi == nodata_ndvi] = np.nan

# --- Dates depuis les descriptions de bandes ---
with rasterio.open(path_ndvi) as src:
    dates = list(src.descriptions)

if not all(dates):
    raise ValueError("Certaines bandes n'ont pas de description (date manquante)")

n_dates = len(dates)

assert ndvi.shape == water.shape, "NDVI et eau doivent avoir les mêmes dimensions"

features = []

with tempfile.TemporaryDirectory() as tmpdir:   #Rasters temporaires qui seront supprimés après
    water_path = os.path.join(tmpdir, "water.tif")
    ndvi_path = os.path.join(tmpdir, "ndvi.tif")

    # --- Boucle temporelle ---
    for i, date_str in enumerate(dates):
        print(f"Traitement {date_str} ({i+1}/{n_dates})")

        # Rasters temporaires
        with rasterio.open(water_path, "w", **water_meta) as dst:
            dst.write(water[i], 1)
        with rasterio.open(ndvi_path, "w", **ndvi_meta) as dst:
            dst.write(ndvi[i], 1)

        # Stats zonales
        zs_water = zonal_stats(
            etangs, water_path,
            stats="mean", nodata=nodata_water, all_touched=True
        )
        zs_ndvi = zonal_stats(
            etangs, ndvi_path,
            stats="mean", nodata=nodata_ndvi, all_touched=True
        )

        # Stockage
        for pond_id, zw, zn in zip(etangs.index, zs_water, zs_ndvi):
            features.append({
                "pond_id": pond_id,
                "date": date_str,
                "freq_eau": zw["mean"],
                "ndvi": zn["mean"],
                "geometry": etangs.loc[pond_id].geometry
            })

    # --- GeoDataFrame ---
    gdf = gpd.GeoDataFrame(features, crs=etangs.crs)

    # --- Reprojection en 4326 pour le web ---
    gdf = gdf.to_crs(epsg=4326)

    # --- Affectation de classes bivariées ---

    ndvi_vals = gdf["ndvi"].dropna().values #sans les NA
    freq_vals = gdf["freq_eau"].dropna().values

    ndvi_bins = np.quantile(ndvi_vals, [0.33, 0.66]) #Division des valeurs en 3 quantiles égaux
    freq_bins = np.quantile(freq_vals, [0.33, 0.66])

    print("Seuils NDVI calculés à partir de l'ensemble des valeurs :", ndvi_bins)
    print("Seuils MNDWI calculés à partir de l'ensemble des valeurs :", freq_bins)

    gdf["ndvi_class"] = np.digitize(gdf["ndvi"], ndvi_bins)
    gdf["freq_class"] = np.digitize(gdf["freq_eau"], freq_bins)

    gdf["bivar_class"] = gdf["ndvi_class"] + 3 * gdf["freq_class"] + 1    #Pour que les classes soient 1-9

    # --- Export GeoJSON ---
    output = "data/etangs_temporal_2018.geojson"
    gdf.to_file(output, driver="GeoJSON")

print(f"GeoJSON temporel créé : {output}")
