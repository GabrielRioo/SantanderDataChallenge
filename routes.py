import locations
import requests
import random
import pandas as pd
from tqdm import tqdm
import pickle
import time
import copy
from collections import Counter

def get_routes(data_path):
    df_routes = pd.read_pickle(data_path+"routes.pkl")
    return df_routes

def get_distance(orgn, dest):
    parameter = ",".join([str(orgn[0]), str(orgn[1])]) + \
        ";" + ",".join([str(dest[0]), str(dest[1])])
    page = ''
    while page == '':
        try:
            page = requests.get(
                url="http://127.0.0.1:5000/route/v1/driving/"+parameter)
            break
        except:
            print("Ops ! connection refused. Let me sleep for 1 second")
            time.sleep(1)
            continue
    data = page.json()
    return data

def convert_text2lnglat(text):
    text = str(text)
    text_list = text[1:-1].split(', ')
    text_list = [float(x) for x in text_list]
    return text_list

def create_routes(data_path, df_locations):
    df_locations_a = df_locations.copy()
    df_locations_a['KEY'] = 0
    df_locations_b = df_locations.copy()
    df_locations_b['KEY'] = 0
    df_routes = df_locations_a.merge(
        df_locations_b, how='outer', on='KEY', suffixes=("_ORIGIN", "_DESTINATION"))
    
    df_routes = df_routes[df_routes.ID_ORIGIN !=
                          df_routes.ID_DESTINATION]
    df_routes = df_routes.drop(columns=['KEY'])
    df_routes = df_routes.reset_index(drop=True)  
    routes_keys = df_routes.ID_ORIGIN.astype(str) + df_routes.ID_DESTINATION.astype(str)
    df_routes["ID"] = routes_keys
    df_routes["DISTANCE"] = -1
    df_routes["DURATION"] = -1
    df_routes["KM_CATEGORY"] = -1
    df_routes["IS_USED"] = 0
    df_routes["IS_CAPTURED"] = 0
    df_routes["LAST_DISTANCE"] = -1
    df_routes["LAST_DURATION"] = -1
    df_routes.to_pickle(data_path+"routes.pkl")
    return df_routes

def get_routes_distance(df_routes):
    list_ids = list(df_routes.index)
    for i in tqdm(list_ids):
        if df_routes.loc[i, "DISTANCE"] == -1:
            orgn = convert_text2lnglat(df_routes.loc[i,["LNGLAT_ORIGIN"]][0])
            dest = convert_text2lnglat(df_routes.loc[i,["LNGLAT_DESTINATION"]][0])
            data = get_distance(orgn, dest)
            distance = data["routes"][0]["distance"]
            duration = data["routes"][0]["duration"]
            df_routes.loc[i, "DISTANCE"] = distance
            df_routes.loc[i, "DURATION"] = duration
            
    df_routes["DISTANCE"] = df_routes.DISTANCE.astype(int)
    df_routes["DURATION"] = df_routes.DURATION.astype(int)
    
    df_routes["KM_CATEGORY"] = df_routes.DISTANCE.apply(lambda x: round( x/1000 * 2) / 2)
    return df_routes

def slice_selected_routes(df_routes):
    df_not_used = df_routes[df_routes.IS_USED == 0]
    df_not_used = df_not_used.drop_duplicates(subset=["CITY_ORIGIN", "CITY_DESTINATION"])
    return df_not_used

def check_selected_routes(df_routes):
    df_used = df_routes[df_routes.IS_USED > 0]
    df_used = df_used.drop_duplicates(subset=["CITY_ORIGIN", "KM_CATEGORY"])
    dict_distance_slctd = dict(df_used.KM_CATEGORY.value_counts().sort_index())
    return df_used, dict_distance_slctd


def update_route_distance(data_path, df_routes, df_selected_routes):
    df_selected_routes.loc[:,"IS_USED"] += 1
    df_routes.loc[df_routes.ID.isin(df_selected_routes.ID),:] = df_selected_routes
    df_routes.to_pickle(data_path+"routes.pkl")
    return df_routes

def prepare_sequence_routes(data_path, df_selected_routes):
    dict_distance_slctd = dict(df_selected_routes.KM_CATEGORY.value_counts().sort_index())
    for k in dict_distance_slctd.keys():
        dict_distance_slctd[k] = {"is_done":0,"count":dict_distance_slctd[k], "ids":list(df_selected_routes[df_selected_routes.KM_CATEGORY == k].ID)}
    original_distance_slctd = copy.deepcopy(dict_distance_slctd)
    pickle.dump(original_distance_slctd, open(data_path+"frequency.pkl", "wb"))
    return dict_distance_slctd

def get_sequence_routes(data_path, dict_distance_slctd, qtd_routes, priority_distances):
    all_routes = list(dict_distance_slctd.keys())
    if sum([x['is_done'] for x in dict_distance_slctd.values()]) > -1*len(dict_distance_slctd.keys()):
        sequence_routes = []
        for k in priority_distances:
            if k in dict_distance_slctd.keys():
                if dict_distance_slctd[k]['ids']:
                    route = dict_distance_slctd[k]['ids'].pop()
                    sequence_routes.append(route)
                    dict_distance_slctd[k]['count'] = len(dict_distance_slctd[k]['ids'])
                else:
                    original = pickle.load(open(data_path+"frequency.pkl", "rb"))
                    dict_distance_slctd[k] = original[k]
                    dict_distance_slctd[k]['is_done'] = -1
                    route = dict_distance_slctd[k]['ids'].pop()
                    sequence_routes.append(route)
                    dict_distance_slctd[k]['count'] = len(dict_distance_slctd[k]['ids'])
        remaining_routes = list(set(all_routes) - set(priority_distances))
        for i in range(0, qtd_routes-len(priority_distances)):
            k = random.choice(remaining_routes)
            if dict_distance_slctd[k]['ids']:
                route = dict_distance_slctd[k]['ids'].pop()
                sequence_routes.append(route)
                dict_distance_slctd[k]['count'] = len(dict_distance_slctd[k]['ids'])
            else:
                original = pickle.load(open(data_path+"frequency.pkl", "rb"))
                if k in original:
                    dict_distance_slctd[k] = original[k]
                    route = dict_distance_slctd[k]['ids'].pop()
                    sequence_routes.append(route)
                    dict_distance_slctd[k]['is_done'] = -1
                    dict_distance_slctd[k]['count'] = len(dict_distance_slctd[k]['ids'])
            remaining_routes.remove(k)
        return sequence_routes
    else:
        return []

def create_selected_routes(data_path):
    df_routes = get_routes(data_path)
    df_selected_routes = slice_selected_routes(df_routes)
    df_selected_routes = get_routes_distance(df_selected_routes)
    df_routes = update_route_distance(data_path, df_routes, df_selected_routes)
    
#     df_selected_routes_filled = fill_selected_routes(df_routes, df_selected_routes)
    
    df_selected_routes.to_pickle(data_path+"selected_routes.pkl")
    return df_routes, df_selected_routes

def get_selected_routes(data_path):
    df_routes = get_routes(data_path)
#     df_selected_routes = pd.read_pickle(data_path+"selected_routes.pkl")
    df_selected_routes = df_routes[df_routes.IS_USED > 0]
    df_selected_routes = df_selected_routes.sample(frac=1).drop_duplicates(subset=["CITY_ORIGIN", "KM_CATEGORY"]).reset_index(drop=True)
    dict_distance_slctd = dict(df_selected_routes.KM_CATEGORY.value_counts().sort_index())
    
    return df_routes, df_selected_routes, dict_distance_slctd

def macro_routes(data_path, df_routes, dict_distance_slctd, qtd_routes, priority_distances):
    sequence_routes_ids = get_sequence_routes(data_path, dict_distance_slctd, qtd_routes, priority_distances)
    if sequence_routes_ids != []:
        df_sequence_routes = df_routes[df_routes.ID.isin(sequence_routes_ids)][["ID", "DISTANCE", "DURATION", "LNGLAT_ORIGIN","LNGLAT_DESTINATION", "KM_CATEGORY"]].sort_values(by="KM_CATEGORY")
        df_sequence_routes.LNGLAT_ORIGIN = df_sequence_routes.LNGLAT_ORIGIN.apply(lambda x: convert_text2lnglat(x))
        df_sequence_routes.LNGLAT_DESTINATION = df_sequence_routes.LNGLAT_DESTINATION.apply(lambda x: convert_text2lnglat(x))
        return df_sequence_routes.reset_index(drop=True)
    else:
        return []
    
def fill_selected_routes(df_routes, df_selected_routes):
    sliced_keys, qtd_sliced = zip(*sorted(Counter(df_selected_routes['KM_CATEGORY']).items(), key=lambda kv: kv[0]))
    df_used = df_routes[df_routes.IS_USED == 1]
    df_used = df_used.drop_duplicates(subset=["CITY_ORIGIN", "KM_CATEGORY"])
    used_keys, qtd_used = zip(*sorted(Counter(df_used['KM_CATEGORY']).items(), key=lambda kv: kv[0]))
    df_filled = df_used[df_used['KM_CATEGORY'].isin(used_keys)]
    
    df_selected_routes_filled = pd.concat([df_filled, df_selected_routes])
    
    return df_selected_routes_filled