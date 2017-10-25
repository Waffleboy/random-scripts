# -*- coding: utf-8 -*-
"""
Created on Tue Nov 22 16:59:31 2016

@author: waffleboy
"""

import pandas as pd
from geopy.geocoders import Nominatim

def remove_extra_details(column):
    new_col = pd.Series(index=column.index,dtype=str)
    for i in column.index:
        address = column[i]
        idx = address.find("Stall")
        if idx:
            new_address = address[:idx]
        else:
            new_address = address
        new_col.set_value(i,new_address)
    return new_col

file = "/home/waffleboy/Desktop/eating.csv"
df = pd.read_csv(file)
col = df["premises_address"]
df["parsed_address"] = remove_extra_details(col)
geolocator = Nominatim()

locations = []
for i in df.index:
    curr_add = df["parsed_address"][i]
    loc = geolocator.geocode(curr_add,exactly_one=True,timeout=10)
    if loc is not None:
        locations.append(loc)
        
lat = [x[0] for x in locations]
long = [x[1] for x in locations]

def generate_heatmap_text(locations):
    s = ''
    for gps_coord in locations:
        lat = gps_coord[0]
        long = gps_coord[1]
        s += "new google.maps.LatLng({},{}),".format(lat,long)
    s = s[:-1] #remove last commar
    return s


