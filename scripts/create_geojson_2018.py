"""
Calcul de stats zonales NDVI et fréquence d'eau par étang et par date,
export en GeoJSON temporel pour webmapping.
"""

import rasterio
import os
import pandas as pd
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

# --- Extraction valeurs zonales hebdomadaires ---
features = []

with tempfile.TemporaryDirectory() as tmpdir:   #Rasters temporaires qui seront supprimés après
    water_path = os.path.join(tmpdir, "mndwi.tif")
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


    # --- Lissage des valeurs par mois ---
    gdf["date"] = pd.to_datetime(gdf["date"])
    gdf["month"] = gdf["date"].dt.to_period("M")

    df_monthly = (
        gdf
        .groupby(["pond_id", "month"], as_index=False)
        .agg({
            "ndvi": "mean",
            "freq_eau": "mean",
            "geometry": "first"
        })
    )

    gdf_monthly = gpd.GeoDataFrame(
        df_monthly,
        geometry="geometry",
        crs=gdf.crs
    )

    gdf_monthly["date"] = gdf_monthly["month"].dt.to_timestamp() + pd.Timedelta(days=14)    #Milieu du mois comme date représentative
    gdf_monthly = gdf_monthly.drop(columns="month")

    gdf_monthly = gdf_monthly.to_crs(epsg=4326)

    # --- Affectation de classes bivariées ---
    ndvi_vals = gdf_monthly["ndvi"].dropna().values
    freq_vals = gdf_monthly["freq_eau"].dropna().values

    ndvi_bins = np.quantile(ndvi_vals, [0.33, 0.66])    #Division des valeurs en 3 quantiles égaux
    freq_bins = np.quantile(freq_vals, [0.33, 0.66])

    gdf_monthly["ndvi_class"] = np.digitize(gdf_monthly["ndvi"], ndvi_bins)
    gdf_monthly["freq_class"] = np.digitize(gdf_monthly["freq_eau"], freq_bins)

    gdf_monthly["bivar_class"] = gdf_monthly["ndvi_class"] + 3 * gdf_monthly["freq_class"] + 1  #Pour que les classes soient 1-9

    gdf_monthly["month_num"] = gdf_monthly["date"].dt.month

    gdf_season = gdf_monthly[
        gdf_monthly["month_num"].between(3, 8)
]
    assec_status = (
        gdf_season
        .groupby("pond_id")["freq_class"]
        .apply(lambda x: (x == 0).all())
    )

    gdf_monthly["assec"] = gdf_monthly["pond_id"].map(assec_status)
    gdf_monthly["assec"] = gdf_monthly["assec"].fillna(False)

    # --- Export GeoJSON ---
    output = "data/etangs_mensuel_2018.geojson"
    gdf_monthly.to_file(output, driver="GeoJSON")


print(f"GeoJSON temporel créé : {output}")