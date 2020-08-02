import json
import geopandas as gpd
import fiona
from shapely import geometry
import matplotlib.pyplot as plt
import glob
from tqdm import tqdm
fiona.supported_drivers['KML'] = 'rw'

def isfloat(x):
    try:
        a = float(x)
        a+=1
    except ValueError:
        return False
    else:
        return True

def isint(x):
    try:
        a = float(x)
        b = int(a)
    except ValueError:
        return False
    else:
        return a == b

def handle_line(line):
    
    line = line.strip().split(" ")
    filtered_line = [l for l in line if isfloat(l) or isint(l)]
    
    if len(filtered_line) > 1:
        return [float(filtered_line[1]), float(filtered_line[0])]
    elif len(filtered_line) == 1:
        return [filtered_line[0]]
    elif filtered_line == []:
        return []

def filter_text(file_path):
    lines = []
    with open(file_path) as f:
        for text in f:
            l = handle_line(text)
            lines.append(l)
    list_lines = [l for l in lines if l != []]
    return list_lines

def convert_list2polygons(list_lines):
    keys = []
    polygons = []
    k = 0
    while(k < len(list_lines)):
        poly = []
        inner_flag = True
        if k == 0:
            line = list_lines[k]
            keys.append(line[0])
            k += 1
        while(inner_flag and k < len(list_lines)):
            line = list_lines[k]
            k += 1
            if len(line) > 1:
                poly.append(line)
            else:
                inner_flag = False
                keys.append(line[0])
        k+= 1
        polygons.append(poly)
    return keys, polygons

def convert_polygons2geojson(keys, polygons, path, filename):
    geojson = {'type': 'FeatureCollection','features': []}
    
    for c in range(0, len(polygons)):
        points = polygons[c]
            
        fea = {'type': 'Feature', 'properties': {'name': keys[c]}, 
               'geometry': {'type': 'Polygon', 'coordinates': [points]}}
        
#         if not keys[c] in removal_list:
        geojson['features'].append(fea)
    with open(path+filename, 'w', encoding='utf8') as f:
        json.dump(geojson, f)
    return geojson

def convert_geojson2kml(path, filename):
    data = gpd.read_file(path+filename, driver="GeoJSON")
    data.to_file(path+filename.replace(".geojson",".kml"), driver="KML")

def convert_log2kml(path, filename):
    list_lines = filter_text(path+filename+".log")
    keys, polygons = convert_list2polygons(list_lines)
    dict_poly = dict(zip(keys, tuple(polygons)))
    keys = list(dict_poly.keys())
    polygons = list(dict_poly.values())
    geojson = convert_polygons2geojson(keys, polygons, path, filename +'.geojson')
    convert_geojson2kml(path, filename+".geojson")

def batch_log2kml(path, pattern):
    files = glob.glob(path+pattern)
    for f in tqdm(files):
        filename = f.replace(path,"").replace(".log","")
        convert_log2kml(path, filename)