import glob
import json
import unidecode
import pandas as pd
from shapely import geometry
import matplotlib.path as mp
import os
from google.cloud import bigquery
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="./bigquery_key.json"

def open_geojson(path, filename):
    with open(path+filename, "r") as f:
        region_geojson = f.readlines()[0]
    return json.loads(region_geojson)

def convert_geojson2polygon(geojson):
    list_polygons = []
    polygon_names = []
    polygon_codenames = []
    for i in range(0, len(geojson["features"])):
        polygon_names.append(geojson["features"][i]['properties']['name'])
        polygon_coordinates = geojson["features"][i]['geometry']['coordinates']
        polygon = polygon_coordinates[0]
        x_y_polygon = [[coord[0], coord[1]] for coord in polygon]
        list_polygons.append(x_y_polygon)
    return list_polygons, polygon_names

def convert_geojsons2dataframe(path, pattern):
    files = glob.glob(path+pattern)
    frames = []
    for f in files:
        filename = f.replace(path,"")
        geojson = open_geojson(path,filename)
        city = f.replace(".geojson","").split("_")[-1].upper()
        list_polygons, polygon_names = convert_geojson2polygon(geojson)
        data = list(zip(list_polygons, polygon_names))
        df = pd.DataFrame(data, columns=['POLYGON', 'ID'])
        df['CITY'] = city
        frames.append(df)
    df_loc = pd.concat(frames)
    df_loc = df_loc.reset_index(drop=True)
    return df_loc

def get_polygon_centroid(polygon):
    poly = geometry.Polygon(polygon)
    return [poly.centroid.x, poly.centroid.y]

def is_inpolygon(dict_polygons, centroid):
    for poly_id, poly in dict_polygons.items():
        polygon_path = mp.Path(poly)
        if polygon_path.contains_point(centroid):
            return poly_id
    return None

def create_locations_dataframe(df_sectors):
    df_aux = df_sectors.copy()
    df_aux["SECTOR_CENTROID"] = df_aux["SECTOR_POLYGON"].apply(lambda x: get_polygon_centroid(x))
    return df_aux[['SECTOR_CENTROID', 'SECTOR_ID', 'CITY']]

def create_locations(data_path, maps_path):
    pattern = "sectors_*.geojson"
    df_sectors = convert_geojsons2dataframe(maps_path, pattern)
    df_sectors = df_sectors.rename(columns={"POLYGON":"SECTOR_POLYGON", "ID": "SECTOR_ID"})

    df_locations = create_locations_dataframe(df_sectors)

    df_sectors.to_csv(data_path+"sectors.csv", sep="\t", index=False)
    df_locations.to_csv(data_path+"locations.csv", sep="\t", index=False)
    df_locations = df_locations.rename(columns={"SECTOR_CENTROID":"LNGLAT","SECTOR_ID":"ID","CITY":"CITY"})
    return df_locations, df_sectors

def get_locations(data_path):
    df_locations = pd.read_csv(data_path+"locations.csv", sep='\t')
    df_sectors = pd.read_csv(data_path+"sectors.csv", sep='\t')
    df_locations = df_locations.rename(columns={"SECTOR_CENTROID":"LNGLAT","SECTOR_ID":"ID","CITY":"CITY"})
    return df_locations, df_sectors

def merge_up_locations(locations_frames, sectors_frames, areas_frames):
    df_all_locations = pd.concat(locations_frames).drop_duplicates(subset=["ID"],keep="first").reset_index(drop=True)
    df_all_sectors = pd.concat(sectors_frames).drop_duplicates(subset=["SECTOR_ID"],keep="first").reset_index(drop=True)
    
    df_new_locations = pd.merge(df_all_locations.rename(columns={"LNGLAT":"CENTROID", "ID":"SUBDISTRICT_ID"}),
                 df_all_sectors[['SECTOR_POLYGON', 'SECTOR_ID']].rename(columns={"SECTOR_ID":"SUBDISTRICT_ID", "SECTOR_POLYGON":"POLYGON"}),
                 on='SUBDISTRICT_ID', 
                 how='inner')
    
    return df_new_locations