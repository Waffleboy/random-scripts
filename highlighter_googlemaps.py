#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  4 14:47:41 2017

@author: waffleboy
"""

from shapely.geometry import Point,Polygon
import json

with open("../admin_level_2.geojson",'r',encoding="utf-8") as f:
    b = json.loads(f.read())
    
borderpolygon = Polygon(b['features'][0]['geometry']['coordinates'][1][0])

def show_on_google_maps(list_of_points,basemap_filepath,save_filepath):
    base = load_base_file(basemap_filepath)
    points = get_formatted_version(list_of_points)
    highlight_map = append_points_to_base(base,points)
    save_file_to_destination(highlight_map,save_filepath)
    return
    
def load_base_file(filepath):
    with open(filepath,'r') as f:
        file = f.read()
    return file

def box_not_in_singapore(box):
    global borderpolygon
    point = Point(box.bottom_right[1],box.bottom_right[0])
    point2 = Point(box.top_right[1],box.top_right[0])
    if borderpolygon.contains(point) and borderpolygon.contains(point2):
        return False
    return True
    
    
def get_formatted_version(list_of_points):
    arr = []
    for box in list_of_points:
        temp_arr = []
        if box_not_in_singapore(box):
            continue
        temp_arr.append(format_into_google_latlong(box.bottom_left))
        temp_arr.append(format_into_google_latlong(box.top_left))
        temp_arr.append(format_into_google_latlong(box.top_right))
        temp_arr.append(format_into_google_latlong(box.bottom_right))
        arr.append(temp_arr)
    return arr

def format_into_google_latlong(coordinates):
    base = 'new google.maps.LatLng({},{})'
    return base.format(coordinates[0],coordinates[1])
    
def append_points_to_base(base,points):
    word = "REPLACE_ME"
    idx = base.find(word)
    highlight_map = base[:idx] + str(points).replace("'",'') + base[idx+len(word):]
    return highlight_map

def save_file_to_destination(highlight_map,save_filepath):
     with open(save_filepath,'w') as f:
        f.write(highlight_map)
     return

    
    