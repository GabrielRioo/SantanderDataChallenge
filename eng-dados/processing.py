from pathlib import Path
from datetime import datetime
from locale import atof
import numpy as np
from PIL import Image
from tqdm import tqdm
import pandas as pd
import pickle
import json
import locale
import pickle
from tqdm import tqdm
from PIL import Image
import sys
from dateutil.parser import parse
import pyocr
import pyocr.builders
import itertools
import pendulum
import os
import pickle
import MTM
import numpy as np
from PIL import Image
import PIL.ImageOps 
import cv2
import matplotlib.pyplot as plt
import glob
import shutil
from shutil import copyfile
import unidecode
import routes

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=Warning)

from google.cloud import bigquery
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="./bigquery_key.json"

def get_images(folder_path):
    return glob.glob(folder_path+'*.png')

def has_time(string):
    return sum([1 if c.isdigit() else 0 for c in string ]) == 4 and len(string) == 4

def hasDigit(string):
    return sum([1 if c.isdigit() else 0 for c in string ]) > 0

def handle_app_info(info, app_name, img_path, labels):
    try:
        prices = [int(float(x.replace('r$',''))*100) for x in info if not has_time(x)]
        image_timestamp = int(img_path.replace(".png","").split("_")[-1])
        img_t = datetime.fromtimestamp(image_timestamp)
        etas = [(img_t.replace(hour=int(x[0:2]), minute=int(x[2:]))-img_t).seconds for x in info if has_time(x)]
        
        if len(etas) != len(prices):
            etas = [int(np.mean(etas)/60) if len(etas) > 0 else '' for i in range(0,len(prices))]
        else:
            etas = [int(eta/60) for eta in etas]
            
        labels = labels[:len(prices)]
        labels_ext = [app_name.capitalize()+x.capitalize() for x in labels]
        head_p = ['modal','service', 'price']
        head_d = ['modal','service', 'duration']
        data_p = list(zip(["ridesharing"]*len(labels), labels_ext, prices))
        data_d = list(zip(["ridesharing"]*len(labels), labels_ext, etas))
        data_result_p = [ dict(zip(head_p, x)) for x in data_p]
        data_result_d = [ dict(zip(head_d, x)) for x in data_d]
        return data_result_p, data_result_d
    except:
        return [], []

def handle_app_est_info(info, app_name, img_path, labels):
    prices_ext = []
    [prices_ext.extend(x.replace("r$","").split("-")) for x in info]
    prices_ext = [int(float(x)*100) for x in prices_ext]
    labels_ext = []
    if len(labels) == 2 and len(prices_ext) == 3:
#         labels_ext.extend([labels[0]+'_min'])
        labels_ext.extend([app_name.capitalize()+labels[0].capitalize()])
#         [labels_ext.extend([app_name.capitalize()+x.capitalize()+'_min', app_name.capitalize()+x.capitalize()+'_max']) for x in labels[1:]]
        [labels_ext.extend([app_name.capitalize()+x.capitalize(), app_name.capitalize()+x.capitalize()]) for x in labels[1:]]
    else:
#         [labels_ext.extend([app_name.capitalize()+x.capitalize()+'_min', app_name.capitalize()+x.capitalize()+'_max']) for x in labels]
        [labels_ext.extend([app_name.capitalize()+x.capitalize(), app_name.capitalize()+x.capitalize()]) for x in labels]
        
    head = ['modal','service', 'price']
    data = list(zip(["ridesharing"]*len(labels_ext), labels_ext, prices_ext))
    data_result = [ dict(zip(head, x)) for x in data]
    if data_result == []:
        return []
    else:
        return data_result
    
def process_image_app(img):
    tools = pyocr.get_available_tools()
    tool = tools[0]
    img_ori = Image.open(img)
    img_array = np.array(img_ori)
    line_and_word_boxes = tool.image_to_string(
        Image.fromarray(img_array[:,:,:]),
        lang="eng",
        builder=pyocr.builders.LineBoxBuilder(tesseract_layout=3)
    )
    text_1 = " ".join([ i.content for i in line_and_word_boxes])
    text_1 = unidecode.unidecode(str(text_1)).lower()
    
    line_and_word_boxes = tool.image_to_string(
        Image.fromarray(img_array[400:,:,:]),
        lang="eng",
        builder=pyocr.builders.LineBoxBuilder(tesseract_layout=3)
    )
    text_2 = " ".join([ i.content for i in line_and_word_boxes])
    text_2 = unidecode.unidecode(str(text_2)).lower()
    text = text_1 + text_2
    app_name = None
    if 'open app' in text:
        return [], []
    elif 'uberx' in text or 'juntos' in text and not 'open app' in text and not 'openapp' in text:
        app_name = 'Uber'
        img_pixels = Image.open(img)
        img_array = np.array(img_pixels)
        if img_pixels.size == (800, 1280):
            img_cropped = Image.fromarray(img_array[200:1000,:,:])
        else:
            img_cropped = Image.fromarray(img_array[300:1539,:,:])
        line_and_word_boxes = tool.image_to_string(
            img_cropped,
            lang="eng",
            builder=pyocr.builders.LineBoxBuilder(tesseract_layout=3)
        )
        text = " ".join([ i.content for i in line_and_word_boxes])
        text = unidecode.unidecode(str(text)).lower()
#         print(text)
        labels = [x for x in text.split(' ') if x == "uberx" or x == "comfort" or x == "juntos" or x == "black" or x == "bag" or x == "flash"]
        labels = [x.replace("uber","") for x in labels]
    elif '99taxi' in text or '99comfort' in text or 'regular taxi' in text and not 'open app' in text and not 'openapp' in text:
        app_name = '99'
        img_pixels = Image.open(img)
        img_array = np.array(img_pixels)
        if img_pixels.size == (800, 1280):
            img_cropped = Image.fromarray(img_array[730:1046,:,:])
        else:
            img_cropped = Image.fromarray(img_array[1090:1569,:,:])
        line_and_word_boxes = tool.image_to_string(
            img_cropped,
            lang="eng",
            builder=pyocr.builders.LineBoxBuilder(tesseract_layout=3)
        )
        text = " ".join([ i.content for i in line_and_word_boxes])
        text = unidecode.unidecode(str(text)).lower().replace("99 taxi","99taxi")
#         print(text)
        labels = ['pop']
        labels.extend([x for x in text.split(' ') if x == "99taxi" or x == "regular" or x == "99comfort" or x == "99entrega"])
#         print(labels)
        if "99comfort" in labels:
            labels.append("99taxi")
        labels = [x.replace("99","") for x in labels]
        text = text.split("metered")[0] + " " + text.split("metered")[-1].replace("r$","")
    else:
        return [], []
    text = text.replace(":", "").replace("eta","").replace("oo","0").replace("o","0").replace("uu","11").replace("u","11")
    text = text.replace("l","1").replace("i","1").replace(",",".").replace("g","0").replace("(","0").replace("c","0")
    list_text = text.split(" ")
    
#     print(labels)
#     print(text)
    clean_list = [x.split('-')[1] if '-' in x else x for x in list_text if has_time(x) or ('r$' in x and '.' in x) or (len(x.split('-')) > 1 and has_time(x.split('-')[1]))]
#     print(clean_list)
    clean_list = remove_discounts(clean_list)
#     print(clean_list)
    return handle_app_info(clean_list, app_name, img, labels)

def remove_discounts(clean_list):
    flag_s = 0
    new_clean_list = []
    for i in clean_list:

        if 'r$' in i:
            flag_s += 1
            if flag_s<2:
                new_clean_list.append(i)
            else:
                new_clean_list.pop()
                new_clean_list.append(i)
                flag_s -= 1
        else:
            flag_s -= 1
            new_clean_list.append(i)
    return new_clean_list

def process_image_app_est(img):
    img_pixels = Image.open(img)
    img_array = np.array(img_pixels)
    try:
        if img_pixels.size == (800, 1280):
            img_cropped = Image.fromarray(img_array[980:,:,:])
        else:
            img_cropped = Image.fromarray(img_array[1520:,:,:])
    except:
        return []
    tools = pyocr.get_available_tools()
    tool = tools[0]
    line_and_word_boxes = tool.image_to_string(
        img_cropped,
        lang="por",
        builder=pyocr.builders.LineBoxBuilder(tesseract_layout=3)
    )
    text = " ".join([ i.content for i in line_and_word_boxes])
    text = unidecode.unidecode(str(text)).lower()
    if not 'open app' and not 'openapp' in text:
        return []
    elif 'uberx' in text and ('open app' in text or 'openapp' in text):
        app_name = 'Uber'
        labels = [x for x in text.split(' ') if x == "uberx" or x == "comfort" or x == "juntos" or x == "black" or x == "uberbag"]
        labels = [x.replace("uber","") for x in labels]
        img_pixels = Image.open(img)
        img_array = np.array(img_pixels)
        line_and_word_boxes = tool.image_to_string(
            img_cropped,
            lang="por",
            builder=pyocr.builders.LineBoxBuilder(tesseract_layout=3)
        )
        text = " ".join([ i.content for i in line_and_word_boxes])
        text = unidecode.unidecode(str(text)).lower()
    elif '99taxi' in text or '99pop' in text and  ('open app' in text or 'openapp' in text):
        app_name = '99'
        labels = ['99pop']
        labels.extend([x for x in text.split(' ') if x == "99taxi" or x == "regular" or x == "99comfort"])
        if "99comfort" in labels:
            labels.append("99taxi")
        labels = [x.replace("99","") for x in labels]
        img_pixels = Image.open(img)
        img_array = np.array(img_pixels)

        line_and_word_boxes = tool.image_to_string(
            img_cropped,
            lang="por",
            builder=pyocr.builders.LineBoxBuilder(tesseract_layout=3)
        )
        text = " ".join([ i.content for i in line_and_word_boxes])
        text = unidecode.unidecode(str(text)).lower()
    else:
        return []
    text = text.replace(":", "").replace("eta","").replace("oo","0").replace("o","0").replace("uu","11").replace("u","11")
    text = text.replace("l","1").replace("i","1").replace(",",".").replace("--","").replace('"',"")
    list_text = text.split(" ")
    clean_list = [x for x in list_text if has_time(x) or 'r$' in x ]
    
    return handle_app_est_info(clean_list, app_name, img, labels)

def handle_modal_info(info, app_name, img_path):
    traffic_duration = [ x for x in info if "hr" in x or "min" in x]
    traffic_distance = [ x for x in info if "km" in x or "m" in x and not "min" in x]
    duration = 0
    for x in traffic_duration:
        if 'hr' in x:
            duration += int(x.replace("hr",""))*60
        elif 'min' in x:
            duration += int(x.replace("min",""))
    distance = 0
    for x in traffic_distance:
        if 'km' in x:
            distance += int(float(x.replace("km",""))*1000)
        elif 'm' in x:
            distance += int(x.replace("m",""))
    json_duration = {"modal": app_name, "service": app_name, "duration": duration}
    json_distance = {"modal": app_name, "service": app_name, "distance": distance}  
    
    if duration == 0 and distance == 0:
        return []
    return json_duration, json_distance

def process_image_modal(img):
    img_pixels = Image.open(img)
    img_array = np.array(img_pixels)
    service = img.split("/")[-1].split("_")[0]
    try:
        if img_pixels.size == (800, 1280):
            if service == 'bus':
                img_cropped = Image.fromarray(img_array[330:590,571:-20,:])
            else:
                img_cropped = Image.fromarray(img_array[1095:1159,:-300,:])
        else:
            if service == 'bus':
                img_cropped = Image.fromarray(img_array[500:640,900:-20,:])
            else:
                img_cropped = Image.fromarray(img_array[1700:1760,:-500,:])
    except:
        return []
    tools = pyocr.get_available_tools()
    tool = tools[0]
    line_and_word_boxes = tool.image_to_string(
        img_cropped,
        lang="eng",
        builder=pyocr.builders.LineBoxBuilder(tesseract_layout=3)
    )
    
    text = " ".join([ i.content for i in line_and_word_boxes])
    text = unidecode.unidecode(str(text)).lower()
    text = text.replace("d4", "(24").replace("i4","14").replace("+","").replace("z","2").replace("tar","").replace("nr","hr").replace("thr","1hr").replace("imin","min")
    text = text.replace("%","6").replace("{","1").replace(". ",".")
    text = text.replace("(","").replace(")","").replace(" min","min").replace(" km","km").replace(" hr","hr").replace(" m ","m ").replace("hr","hr ").replace("omin","min").replace(" m","m")
#     print(text)
    traffic_info = [ x for x in text.split(" ") if ("min" in x or "km" in x or "hr" in x or "m" in x) and (not "r$" in x) and hasDigit(x)]
    return handle_modal_info(traffic_info, service, img)

def batch_process_app(images_path, logs_path):
    type_image = 'app'
    if not os.path.exists(logs_path):
        os.makedirs(logs_path)
    full_images_path = images_path+type_image+'/'
    full_logs_path = logs_path+type_image+'/'
    images_files = get_images(full_images_path)
    if not os.path.exists(full_logs_path):
        os.makedirs(full_logs_path)
    price_data_rows = []
    duration_data_rows = []
    for img in tqdm(images_files):
        img_metadata = img.replace(".png","").split("/")[-1].split("_")
        city = images_path.split("/")[1].split("_")[1]
        km_category = img_metadata[-5]
        route_id = img_metadata[-4]
        ts = int(img_metadata[-1])
        date_ts =  datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        try:
            info_data = process_image_app(img)
        except:
            info_data = ([],[])
        if info_data == ([], []):
            copyfile(img, img.replace(full_images_path, full_logs_path))
        else:
            price_data = info_data[0]
            duration_data = info_data[1]
            price_ext = [{**r, **{'km_category':km_category,'route_id':route_id,'capture_time':date_ts, 'city':city, 'image_id':img}} for r in price_data]
            duration_ext = [{**r, **{'km_category':km_category,'route_id':route_id,'capture_time':date_ts, 'city':city, 'image_id':img}} for r in duration_data]
            price_data_rows.extend(price_ext)
            duration_data_rows.extend(duration_ext)
    return pd.DataFrame(price_data_rows), pd.DataFrame(duration_data_rows)

def batch_process_appest(images_path, logs_path):
    type_image = 'app_est'
    if not os.path.exists(logs_path):
        os.makedirs(logs_path)
    full_images_path = images_path+type_image+'/'
    full_logs_path = logs_path+type_image+'/'
    images_files = get_images(full_images_path)
    if not os.path.exists(full_logs_path):
        os.makedirs(full_logs_path)
    price_data_rows = []
    duration_data_rows = []
    for img in tqdm(images_files):
        img_metadata = img.replace(".png","").split("/")[-1].split("_")
        city = images_path.split("/")[1].split("_")[1]
        km_category = img_metadata[-5]
        route_id = img_metadata[-4]
        ts = int(img_metadata[-1])
        date_ts =  datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        try:
            info_data = process_image_app_est(img)
        except:
            info_data = []
        if info_data == []:
            copyfile(img, img.replace(full_images_path, full_logs_path))
        else:
            price_data = info_data
            price_ext = [{**r, **{'km_category':km_category,'route_id':route_id,'capture_time':date_ts, 'city':city, 'image_id':img}} for r in price_data]
            price_data_rows.extend(price_ext)
    return pd.DataFrame(price_data_rows)

def batch_process_modal(images_path, logs_path):
    type_image = 'modal'
    if not os.path.exists(logs_path):
        os.makedirs(logs_path)
    full_images_path = images_path+type_image+'/'
    full_logs_path = logs_path+type_image+'/'
    images_files = get_images(full_images_path)
    if not os.path.exists(full_logs_path):
        os.makedirs(full_logs_path)
    duration_data_rows = []
    distance_data_rows = []    
    for img in tqdm(images_files):
        img_metadata = img.replace(".png","").split("/")[-1].split("_")
        city = images_path.split("/")[1].split("_")[1]
        km_category = img_metadata[-5]
        route_id = img_metadata[-4]
        ts = int(img_metadata[-1])
#         city = 
        date_ts =  datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        try:
            info_data = process_image_modal(img)
        except:
            info_data = []
        if info_data == []:
            copyfile(img, img.replace(full_images_path, full_logs_path))
        else:
            duration_data = [info_data[0]]
            distance_data = [info_data[1]]
            duration_ext = [{**r, **{'km_category':km_category,'route_id':route_id,'capture_time':date_ts, 'city':city, 'image_id':img}} for r in duration_data]
            distance_ext = [{**r, **{'km_category':km_category,'route_id':route_id,'capture_time':date_ts, 'city':city, 'image_id':img}} for r in distance_data]
            duration_data_rows.extend(duration_ext)
            distance_data_rows.extend(distance_ext)
    return pd.DataFrame(duration_data_rows), pd.DataFrame(distance_data_rows)


def df2csv(df, data_path, dataset_path, set_name):
    
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    set_path = dataset_path+set_name+"s/"
    
    if not os.path.exists(set_path):
        os.makedirs(set_path)
        
    df = df.drop_duplicates()
    now = datetime.now()
    timestamp = now.strftime("%d-%m-%Y_%H-%M-%S")
    
    src = set_path+set_name+'_'+timestamp+'.csv'
    
    df = df.rename(columns=lambda x: x.replace(" ","_").upper())
    
#     df_filtered = filter_move_outlayers(df, set_name.upper())
    
    df_routes = routes.get_routes(data_path)
    df_new = prep_df(df, df_routes)
    
    for c in df_new.columns:
        df_new[c] = df_new[c].fillna("")
        df_new[c] = df_new[c].astype(str)

    df_new.to_csv(src, sep='\t', index=False)
    
    return df_new
    
def filter_dump_files(data_path, dataset_path, df_prices, df_durations, df_distances, files, delete_flag):

    df_new_prices = df2csv(df_prices, data_path, dataset_path, 'price')
    df_new_durations = df2csv(df_durations, data_path, dataset_path, 'duration')
    df_new_distances = df2csv(df_distances, data_path, dataset_path, 'distance')
    
    if delete_flag:
        for f in files:
            os.remove(f)
    return df_new_prices, df_new_durations, df_new_distances
    
def filter_move_outlayers(df, type_c):

    
    km_categories = set(df.KM_CATEGORY)
    services = set(df.SERVICE)
    
    frames_filtered = []
    frames_erros = []
    
    df[type_c] = pd.to_numeric(df[type_c], errors='coerce')
    df = df.dropna()
    
    if type_c == "PRICE":
        df = df[(df['PRICE'].astype(int) < 10000)]

    for km in km_categories:
        for ser in services:
            df_stats = df.groupby(["KM_CATEGORY", "SERVICE"]).mean().reset_index()
            mu = float(df_stats[(df_stats.KM_CATEGORY==km)&(df_stats.SERVICE==ser)][type_c].mean())
            df_ser_filtered = df[(df.KM_CATEGORY==km)&(df.SERVICE==ser)&((df[type_c] < 5*mu)&(df[type_c] > mu/5))]
            df_ser_errors = df[(df.KM_CATEGORY==km)&(df.SERVICE==ser)&((df[type_c] > 5*mu)|(df[type_c] < mu/5))]
            
            frames_filtered.append(df_ser_filtered)
            frames_erros.append(df_ser_errors)
    
    df_good = pd.concat(frames_filtered)
    
    df_good[type_c] = df_good[type_c].astype(int)
    df_good[type_c] = df_good[type_c].astype(str)
    
    df_bad = pd.concat(frames_erros)
    
    for img in df_bad['IMAGE_ID']:
        copyfile(img, img.replace("/images/","/logs/"))
        
    return df_good


def prep_df(df, df_routes):
    df_aux_1 = df.drop(columns=["CITY"])
    df_aux_routes = df_routes[["ID", "ID_ORIGIN", "CITY_ORIGIN", "ID_DESTINATION", "CITY_DESTINATION"]].rename(columns={"ID":"ROUTE_ID", "ID_ORIGIN":"SUBDISTRICT_ID_ORIGIN", "ID_DESTINATION": "SUBDISTRICT_ID_DESTINATION"})
    
    df_new = pd.merge(df_aux_routes,
                 df_aux_1,
                 on='ROUTE_ID', 
                 how='inner')
    return df_new

