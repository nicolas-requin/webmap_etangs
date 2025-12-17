"""
Script permettant de découper des rasters selon les polygones d'un shapefile représentant des étangs.
Le programme :

1. Charge un shapefile et vérifie son système de coordonnées (CRS).
2. Définit un CRS par défaut si absent, puis reprojette le shapefile vers celui des rasters à découper.
3. Extrait les géométries des polygones afin de les utiliser comme masque.
4. Définit une fonction crop_raster() qui :
   - applique un masque sur un raster à partir des géométries du shapefile,
   - met à jour les métadonnées (dimensions, transform),
   - recopie les descriptions des bandes si elles existent,
   - écrit le raster découpé sur disque.
5. Applique cette fonction pour produire deux rasters découpés :
   un NDVI et un MNDWI.
"""

import rasterio
from rasterio.mask import mask
import geopandas as gpd

# --- Fichiers sources ---
path_shp = "../mini_etangs.shp"  # ton shapefile réduit
path_ndvi = "../indices/NDVI_2023.tif"
path_water = "../indices/MNDWI_2023.tif"

# --- Charger le shapefile ---
etangs = gpd.read_file(path_shp)

# Si le CRS est manquant, on le définit manuellement
if etangs.crs is None:
    etangs.set_crs(epsg=2154, inplace=True)  # 🔹 adapte le code EPSG selon ton shapefile

# Puis on reprojette si nécessaire
with rasterio.open(path_ndvi) as src_ref:
    crs_raster = src_ref.crs
if etangs.crs != crs_raster:
    print("Reprojection du shapefile vers le CRS du raster...")
    etangs = etangs.to_crs(crs_raster)

# S’assurer que la projection est la même que celle du raster NDVI
with rasterio.open(path_ndvi) as src:
    crs_raster = src.crs
etangs = etangs.to_crs(crs_raster)

# Extraire la géométrie (tous les polygones)
geoms = [geom.__geo_interface__ for geom in etangs.geometry]

# --- Fonction de découpe ---
def crop_raster(input_path, output_path, geometries):
    with rasterio.open(input_path) as src:
        out_image, out_transform = mask(src, geometries, crop=True)
        out_meta = src.meta.copy()
        out_meta.update({
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })

        # Copier les descriptions des bandes (si présentes)
        band_descriptions = []
        try:
            band_descriptions = [src.descriptions[i] for i in range(src.count)]
        except Exception:
            pass  # au cas où il n’y a pas de description

    # --- Écriture du raster découpé ---
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(out_image)
        # Réappliquer les descriptions à chaque bande
        if band_descriptions:
            for i, desc in enumerate(band_descriptions, start=1):
                dest.set_band_description(i, desc)

    print(f"Raster découpé : {output_path} (bandes = {len(band_descriptions)})")


# --- Découpe NDVI et masque eau ---
crop_raster(path_ndvi, "NDVI_2023_test.tif", geoms)
crop_raster(path_water, "MNDWI_2023_test.tif", geoms)