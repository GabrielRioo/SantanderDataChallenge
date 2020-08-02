import time
from tqdm import tqdm
import subprocess
from datetime import datetime, timedelta
import os
import routes

adb_path = "adb"

def dd2dms(deg, coor):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    if coor == "latitude":
        return "".join([str(abs(d)),"%s", str(m),"%s", str(round(sd,2)), "S"])
    else:
        return "".join([str(abs(d)),"%s", str(m),"%s", str(round(sd,2)), "W"])

def close_gmaps(device, timestamp):
    subprocess.Popen(adb_path+" -s %s shell am force-stop com.google.android.apps.maps"%(device),shell=True,stdout=subprocess.PIPE)
    time.sleep(timestamp)

def close_uber(device, timestamp):
    subprocess.Popen(adb_path+" -s %s shell am force-stop com.ubercab"%(device),shell=True,stdout=subprocess.PIPE)
    time.sleep(timestamp)

def tap_swipeup(device, x1, y1, x2, y2, ms, sl):
    subprocess.Popen(adb_path+" -s %s shell input swipe %s %s %s %s %s"%(device, x1, y1, x2, y2, ms*1000),shell=True,stdout=subprocess.PIPE)
    time.sleep(sl)

def tap_screen(device,x,y, timestamp):
    subprocess.Popen(adb_path+" -s %s shell input tap %s %s"%(device,x,y),shell=True,stdout=subprocess.PIPE)
    time.sleep(timestamp)

def send_keyevent(device, key, timestamp):
    subprocess.Popen(adb_path+" -s %s shell input keyevent %s"%(device, key),shell=True,stdout=subprocess.PIPE)
    time.sleep(timestamp)

def input_text(device, text, timestamp):
    subprocess.Popen(adb_path+" -s %s shell input text %s"%(device, text),shell=True,stdout=subprocess.PIPE)
    time.sleep(timestamp)

def take_screenshot(device, timestamp):
    time.sleep(timestamp)
    fin_path = "../sdcard/screencap.png"
    subprocess.Popen(adb_path+" -s %s shell screencap -p %s "%(device,fin_path),shell=True,stdout=subprocess.PIPE)
    time.sleep(timestamp)

def save_screenshot(device, fout_path, timestamp):
    fin_path = "../sdcard/screencap.png"
    subprocess.Popen(adb_path+" -s %s pull %s %s"%(device,fin_path,fout_path),shell=True,stdout=subprocess.PIPE)
    time.sleep(timestamp)

def genFilepath(images_path, f_path, filename, route, version, device):
    # Generate Image Path
    folder_path = images_path+f_path+"/"
    city = folder_path.split("/")[1].split('_')[1]
    route_name = route.ID
    distance = route.KM_CATEGORY
    now = datetime.now()
    timestamp = datetime.timestamp(now)
    date_str = now.strftime("%Y-%m-%d_%H-%M")

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    device = device.replace(".","-").replace(":","-")
    final_path = folder_path+"_".join([filename, version, device, str(distance), str(route_name), date_str, str(int(timestamp))])+".png"
    print(city.upper()+" "+device.ljust(20)+" Another one! "+str(distance).ljust(2)+" Km route "+filename.ljust(20)+now.strftime("%H:%M"))

    return final_path

def tap_swipeleft(device, x1, y1, x2, y2, ms, sl):
    subprocess.Popen(adb_path+" -s %s shell input swipe %s %s %s %s %s"%(device, x1, y1, x2, y2, ms*1000),shell=True,stdout=subprocess.PIPE)
    time.sleep(sl)

def sleep_time():
    now = datetime.now()
    next_time = now.replace(minute=0, second=0)+ timedelta(hours=1)
    time_s = (next_time-now).seconds
    print("Sleep! see you in "+str(time_s).rjust(25)+" seconds")
    time.sleep(time_s)

def route_simulation_1(device, version, df_routes, df_selected_routes, data_path, maps_path, images_path, qtd_routes, priority_distances):

    dict_distance_slctd = routes.prepare_sequence_routes(data_path, df_selected_routes)
    df_selected = routes.macro_routes(data_path, df_routes, dict_distance_slctd, qtd_routes, priority_distances)
    city = images_path.split("/")[1].split('_')[1]
    while len(df_selected) > 0:
        for route in df_selected.itertuples():
            start = time.time()
            
            send_keyevent(device, "KEYCODE_APP_SWITCH", 2)
            tap_screen(device, 600, 1600, 2)
            send_keyevent(device, "KEYCODE_HOME", 2)

            origin_lat = str(route.LNGLAT_ORIGIN[1])
            origin_lon = str(route.LNGLAT_ORIGIN[0])
            origin = origin_lat+",%s"+origin_lon
            destination_lat =  str(route.LNGLAT_DESTINATION[1])
            destination_lon =  str(route.LNGLAT_DESTINATION[0])
            destination = destination_lat+",%s"+destination_lon

            close_gmaps(device, 1)
            tap_screen(device,980,1750, 20) # Open Maps
            tap_screen(device,600,110, 5) # Activate Destination
            input_text(device, origin, 10) # Enter Origin
            # tap_screen(device,500,180, 8) # Select
            tap_screen(device,1100,1630, 20) # Click Search Keyboards
            tap_screen(device,150,1850, 5) # Direction
            tap_screen(device,570,90, 5) # Activate Origin
            tap_screen(device,570,90, 5) # Activate Origin
            input_text(device, destination, 10) # Enter Origin
            # tap_screen(device,500,180, 8) # Select
            tap_screen(device,1100,1630, 15) # Click Search Keyboards
            tap_screen(device,1150,180, 5) # Invert

            tap_screen(device,100,270, 5)
            take_screenshot(device, 2)
            car_final_path =  genFilepath(images_path, "modal", "car", route, version, device)
            save_screenshot(device, car_final_path, 2)

            tap_screen(device,310,270, 5)
            take_screenshot(device, 2)
            moto_final_path =  genFilepath(images_path, "modal", "motocycle", route, version, device)
            save_screenshot(device, moto_final_path, 2)

            tap_screen(device,520,270, 5)
            take_screenshot(device, 2)
            bus_final_path =  genFilepath(images_path, "modal", "bus", route, version, device)
            save_screenshot(device, bus_final_path, 2)

            tap_screen(device,720,270, 5)
            take_screenshot(device, 2)
            walk_final_path =  genFilepath(images_path, "modal", "walk", route, version, device)
            save_screenshot(device, walk_final_path, 2)

            tap_screen(device,1100,270, 5)
            take_screenshot(device, 2)
            bike_final_path =  genFilepath(images_path, "modal", "bicycle", route, version, device)
            save_screenshot(device, bike_final_path, 2)

            tap_screen(device,920,270, 2)

            tap_screen(device,300,1550, 5)
            take_screenshot(device, 2)
            app1_est_final_path =  genFilepath(images_path, "app_est" ,"app_est", route, version, device)
            save_screenshot(device, app1_est_final_path, 2)

            tap_screen(device,920,1550, 5)
            take_screenshot(device, 2)
            app2_est_final_path =  genFilepath(images_path, "app_est" ,"app_est", route, version, device)
            save_screenshot(device, app2_est_final_path, 2)

            tap_screen(device,300,1550, 5)
            tap_screen(device,600,1870, 25)
            tap_swipeup(device, 800, 1440, 800, 90, 1, 2)
            tap_swipeup(device, 800, 1440, 800, 90, 1, 2)
            tap_swipeleft(device, 1100, 1534, 950, 1534, 1, 2)

            take_screenshot(device, 2)
            app1_final_path =  genFilepath(images_path, "app" ,"app", route, version, device)
            save_screenshot(device, app1_final_path, 2)

            send_keyevent(device, "KEYCODE_HOME", 4)
            tap_screen(device,980,1800, 10)

            tap_screen(device,920,1550, 5)
            tap_screen(device,600,1870, 25)
            tap_swipeup(device, 800, 1440, 800, 90, 1, 2)
            tap_swipeup(device, 800, 1440, 800, 90, 1, 2)
            tap_swipeleft(device, 1100, 1534, 950, 1534, 1, 2)

            take_screenshot(device, 2)
            app2_final_path =  genFilepath(images_path, "app", "app", route, version, device)
            save_screenshot(device, app2_final_path, 2)

            send_keyevent(device, "KEYCODE_HOME", 4)
            close_uber(device,1) 

            send_keyevent(device, "KEYCODE_APP_SWITCH", 2) # All open apps
            tap_screen(device, 600, 1600, 2) # Close All
            tap_screen(device,600,1750, 20) # Open Uber
            # tap_swipeup(device, 800, 1670, 800, 90, 1, 2)
            tap_screen(device,580,1325, 5) # Where to?
            tap_screen(device,580,140, 2) # Home
            tap_screen(device,580,140, 2) # Home
            tap_screen(device,1060,140, 2) # Clear
            tap_screen(device,580,140, 2) # Home
            input_text(device, origin, 10) # Enter Origin
            tap_screen(device,1100,1630, 15) # Click Search Keyboards
            tap_screen(device,580,320, 10) # Select Origin
            input_text(device, destination, 10) # Enter Destination
            tap_screen(device,1100,1630, 15) # Click Search Keyboards
            tap_screen(device,580,320, 10) # Select Destination
            tap_swipeup(device, 800, 1440, 800, 90, 1, 2)
            
            take_screenshot(device, 2)
            app1_final_path =  genFilepath(images_path, "app" ,"uber", route, version, device)
            save_screenshot(device, app1_final_path, 2)
            
            end = time.time()
            print("Finished! "+city+" in "+str(end-start).ljust(15)+" seconds")
            
        print("Finished "+city+" routes selection!"+":)".rjust(33))
        route = routes.macro_routes(data_path, df_routes, dict_distance_slctd, qtd_routes, priority_distances)
        sleep_time()

def route_simulation_2(device, version, df_routes, df_selected_routes, data_path, maps_path, images_path, qtd_routes, priority_distances):
    
    dict_distance_slctd = routes.prepare_sequence_routes(data_path, df_selected_routes)
    df_selected = routes.macro_routes(data_path, df_routes, dict_distance_slctd, qtd_routes, priority_distances)
    city = images_path.split("/")[1].split('_')[1]
    while len(df_selected) > 0:
        for route in df_selected.itertuples():
            start = time.time()
            
            send_keyevent(device, "KEYCODE_APP_SWITCH", 2)
            tap_screen(device, 400, 980, 2) # Close All
            send_keyevent(device, "KEYCODE_HOME", 2)

            origin_lat = str(route.LNGLAT_ORIGIN[1])
            origin_lon = str(route.LNGLAT_ORIGIN[0])
            origin = origin_lat+",%s"+origin_lon
            destination_lat =  str(route.LNGLAT_DESTINATION[1])
            destination_lon =  str(route.LNGLAT_DESTINATION[0])
            destination = destination_lat+",%s"+destination_lon

            close_gmaps(device, 1)
            tap_screen(device,650,1170, 20) # Open Maps
            tap_screen(device,450,80, 5) # Activate Destination
            input_text(device, origin, 10) # Enter Origin
            tap_screen(device,740,1050, 20) # Click Search Keyboards
            # tap_screen(device,450,180, 8) # Select
            tap_screen(device,140,1220, 5) # Direction
            tap_screen(device,450,80, 5) # Activate Origim
            tap_screen(device,450,80, 5) # Activate Origim
            input_text(device, destination, 10) # Enter Destination
            tap_screen(device,740,1050, 20) # Click Search Keyboards
            # tap_screen(device,450,180, 8) # Select
            tap_screen(device,760,150, 5) # Invert

            tap_screen(device,100,200, 5)
            take_screenshot(device, 2)
            car_final_path =  genFilepath(images_path, "modal", "car", route, version, device)
            save_screenshot(device, car_final_path, 2)

            tap_screen(device,200,200, 5)
            take_screenshot(device, 2)
            moto_final_path =  genFilepath(images_path, "modal", "mocycle", route, version, device)
            save_screenshot(device, moto_final_path, 2)

            tap_screen(device,350,200, 5)
            take_screenshot(device, 2)
            bus_final_path =  genFilepath(images_path, "modal", "bus", route, version, device)
            save_screenshot(device, bus_final_path, 2)

            tap_screen(device,470,200, 5)
            take_screenshot(device, 2)
            walk_final_path =  genFilepath(images_path, "modal", "walk", route, version, device)
            save_screenshot(device, walk_final_path, 2)

            tap_screen(device,720,200, 5)
            take_screenshot(device, 2)
            bike_final_path =  genFilepath(images_path, "modal", "bicycle", route, version, device)
            save_screenshot(device, bike_final_path, 2)

            tap_screen(device,600,200, 2)

            tap_screen(device,200,1000, 5)
            take_screenshot(device, 2)
            app1_est_final_path =  genFilepath(images_path, "app_est" ,"app_est", route, version, device)
            save_screenshot(device, app1_est_final_path, 2)

            tap_screen(device,600,1000, 5)
            take_screenshot(device, 2)
            app2_est_final_path =  genFilepath(images_path, "app_est" ,"app_est", route, version, device)
            save_screenshot(device, app2_est_final_path, 2)

            tap_screen(device,200,1000, 5)
            tap_screen(device,400,1250, 25)
            tap_swipeup(device, 400, 910, 400, 60, 1, 2)
            tap_swipeup(device, 400, 910, 400, 60, 1, 2)
            tap_swipeleft(device, 750, 1020, 640, 1020, 1, 2)

            take_screenshot(device, 2)
            app1_final_path =  genFilepath(images_path, "app" ,"app", route, version, device)
            save_screenshot(device, app1_final_path, 2)

            send_keyevent(device, "KEYCODE_HOME", 4)
            tap_screen(device,650,1170, 8) # Open Maps

            tap_screen(device,600,1000, 5)
            tap_screen(device,400,1250, 25)
            tap_swipeup(device, 400, 910, 400, 60, 1, 2)
            tap_swipeup(device, 400, 910, 400, 60, 1, 2)
            tap_swipeleft(device, 750, 1020, 640, 1020, 1, 2)

            take_screenshot(device, 2)
            app2_final_path =  genFilepath(images_path, "app", "app", route, version, device)
            save_screenshot(device, app2_final_path, 2)

            send_keyevent(device, "KEYCODE_HOME", 4)
            close_uber(device,1) 

            send_keyevent(device, "KEYCODE_APP_SWITCH", 2) # All open apps
            tap_screen(device, 400, 980, 2) # Close All
            tap_screen(device,400,1170, 20) # Open Uber
            # tap_swipeup(device, 400, 1080, 400, 60, 1, 2)
            tap_screen(device,400,825, 5) # Where to?
            tap_screen(device,400,100, 2) # Home
            tap_screen(device,400,100, 2) # Home
            tap_screen(device,705,100, 2) # Clear
            tap_screen(device,400,100, 2) # Home
            input_text(device, origin, 10) # Enter Origin
            tap_screen(device,740,1050, 15) # Click Search Keyboards
            tap_screen(device,400,240, 10) # Select Origin
            input_text(device, destination, 10) # Enter Destination
            tap_screen(device,740,1050, 15) # Click Search Keyboards
            tap_screen(device,400,240, 10) # Select Destination
            tap_swipeup(device, 400, 910, 400, 60, 1, 2)
            
            take_screenshot(device, 2)
            app1_final_path =  genFilepath(images_path, "app" ,"uber", route, version, device)
            save_screenshot(device, app1_final_path, 2)
            
            end = time.time()
            print("Finished! "+city+" in "+str(end-start).ljust(15)+" seconds")
            
        print("Finished "+city+" routes selection!"+":)".rjust(33))
        route = routes.macro_routes(data_path, df_routes, dict_distance_slctd, qtd_routes, priority_distances)
        sleep_time()

def handle_route_simulation(resolution,device, version, df_routes, df_selected_routes, data_path, maps_path, images_path, qtd_routes, priority_distances):
    if resolution == "1200":
        return route_simulation_1(device, version, df_routes, df_selected_routes, data_path, maps_path, images_path, qtd_routes, priority_distances)
    elif resolution == "800":
        return route_simulation_2(device, version, df_routes, df_selected_routes, data_path, maps_path, images_path, qtd_routes, priority_distances)