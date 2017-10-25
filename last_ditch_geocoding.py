#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  6 17:14:40 2017

@author: waffleboy
"""

import requests
import pandas as pd
from pandas import ExcelWriter

#df = pd.read_excel("../raw_data/cleaning_schedule_final_geocoded.xlsx")
df = pd.read_excel("../raw_data/cleaning_3quarter_regeocoded.xlsx")
#
#df["latitude"] = pd.Series(index = df.index,dtype=float)
#df["longitude"] = pd.Series(index = df.index,dtype=float)

BASE = "https://developers.onemap.sg/commonapi/search?searchVal={}&returnGeom={}&getAddrDetails={}"
wdir = "../"
def calculate_missing(df):
    missing = sum(df["latitude"].isnull())
    total = round((missing / len(df))*100,2)
    print("Total missing: {},{}%".format(missing,total))


def save_df(df,filename):
    global wdir
    writer = ExcelWriter(wdir+'raw_data/{}.xlsx'.format(filename))
    df.to_excel(writer,index=False)
    writer.save()
    
def onemap_geocode(location):
    req = requests.get(BASE.format(location,"Y","Y"))
    json = req.json()
    return json
    
def calculate_resolved_statistics(attempted,resolved):
    percentage = round((resolved/ attempted)*100,2)
    print("Resolved {} / {}, {}%".format(resolved,attempted,percentage))
    
column = "cleaned_column"
attempted = 0
resolved = 0
calculate_missing(df)
# Actual running
for i in df.index:
    latitude = df["latitude"][i]
    if pd.isnull(latitude):
        location = df[column][i]#.replace('&','')
        location_json = onemap_geocode(location)
        attempted += 1
        if location_json["found"]:
            results = location_json["results"]
            #take first result
            first_result = results[0]
            lat = first_result["LATITUDE"]
            long = first_result["LONGITUDE"]
            df["latitude"].set_value(i,lat)
            df["longitude"].set_value(i,long)
            resolved += 1

calculate_resolved_statistics(attempted,resolved)
calculate_missing(df)

#==============================================================================
#                               Google
#==============================================================================

from geopy.geocoders import GoogleV3

def in_singapore(lat,long):
    if lat > 1.22 and lat <= 1.47:
        if long > 103.6 and long <= 105.04:
            return True
    return False

def initialize_google(key_index):
    keys = ["AIzaSyCxB_FgVW4meat7vsfXulNh3eGB1mPrTdI",\
            "AIzaSyCWC988fyeewFRL_xQPNaV0xHX3T_MKgRk",\
    'AIzaSyB0PFccCHj6KtTt6yHaaDnId4Jyz6ARCCg',\
    'AIzaSyDYA-h7g-zhSzFzpSg0mEYdgVvm3AGtbEU',#shawn
    "AIzaSyA-aCrbHCfDMQzA-PEBMR9n-1UDBHiiOAk",\
    'AIzaSyDfy1qWewEp2O1n4_WkkH-qbJU5rJU_pAM',\
    "AIzaSyCYUIActiOs_m391b0OLRTr7NCz6GpF5Ig",#khai
    "AIzaSyA4p2UkeKL2UUrBmzDs8lmoQ5-o5uT8TlA"]  #tewan
    key = keys[key_index]
    g = GoogleV3(key)
    return g
    
key_index = 0
g = initialize_google(key_index)
attempted = 0
resolved = 0

for i in df.index:
    latitude = df["latitude"][i]
    if pd.isnull(latitude):
        if attempted % 2490 == 0:
            key_index += 1
            g = initialize_google(key_index)
        location = df[column][i].replace('&','')
        attempted += 1
        loc = g.geocode(location,region='sg',timeout=10)
        if loc:
            lat = loc.latitude
            long = loc.longitude
            if in_singapore(lat,long):
                df["latitude"].set_value(i,lat)
                df["longitude"].set_value(i,long)
                resolved += 1
                
calculate_resolved_statistics(attempted,resolved)
