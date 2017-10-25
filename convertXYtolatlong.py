#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 17:11:52 2016

@author: waffleboy
"""

import pandas as pd
from SVY21 import *
wdir = "/home/waffleboy/Desktop/NEA/raw_data/"
df = pd.read_excel(wdir+"feedback_combined.xlsx")

cv = SVY21()

## Add latlong to feedback --> convert from arcgis 
def convert_XY_to_latlong(x,y):
    global cv
    lat,long = cv.computeLatLon(x,y)
    return lat,long

latCol = pd.Series(index = df.index,dtype=float)
longCol = pd.Series(index = df.index,dtype=float)

for i in df.index:
    x = df["X Coordinates"][i]
    y = df["Y Coordinates"][i]
    lat,long = convert_XY_to_latlong(x,y)
    latCol.set_value(i,lat)
    longCol.set_value(i,long)

df["lat"] = latCol
df["long"] = longCol

from pandas import ExcelWriter
writer = ExcelWriter(wdir+'feedback_latlong.xlsx')
df.to_excel(writer,index=False)
writer.save()
###################################################
    

# This should be a seperate file
df2 = pd.read_excel(wdir+"EEMS.xlsx")
df2["Offence-Date"] = pd.to_datetime(df2["Offence-Date"])

#remove smoking
df2 = df2[df2["UF-Enforcement Sub-Category"] != "Smoking(Smoker)"]


from geopy.geocoders import GoogleV3
import datetime

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


# used for differnet date ranges
def calculate_postal_code_satistics(df2):
    total_postal_codes = len(df2["Offence-Postal"])
    unique_postal_codes = len(df2["Offence-Postal"].value_counts())
    missing_postal_codes = sum(pd.isnull(df2["Offence-Postal"]))
    
    print("Total postal codes: {}".format(total_postal_codes)) # 123394 total postal codes
    print("Total Unique postal codes: {}".format(unique_postal_codes))
    print("Unique ratio: {}%".format(round((unique_postal_codes/total_postal_codes)*100,2)))
    print("Missing postal codes: {} - {}%".format(missing_postal_codes,round((missing_postal_codes/total_postal_codes)*100,2)))
    
def subset_df_on_date_range(df,begin_date,end_date):
    mask = (df["Offence-Date"] >= begin_date) & (df["Offence-Date"] <= end_date)
    return df.loc[mask]

calculate_postal_code_satistics(df2)
#
#print("For 2015")
#df_2015 = subset_df_on_date_range(df2,datetime.date(2015,1,1),datetime.date(2015,12,31))
#calculate_postal_code_satistics(df_2015)


def get_unique_postal_codes(df):
    return [str(int(x)) for x in df["Offence-Postal"].unique() if (pd.isnull(x) == False)]

## Geocode the postal codes - RUNME
unique_postal_codes = get_unique_postal_codes(df2)

key_counter = 0
g = initialize_google(key_counter)

postal_code_latlong_lst = joblib.load("postalcodes.pkl") #[]

for i in range(1873,len(unique_postal_codes)):
    try:
        if i != 0 and i % 2499 == 0:
            key_counter += 1
            g = initialize_google(key_counter)
        
        postal_code = unique_postal_codes[i]
        loc = g.geocode(postal_code + " Singapore",timeout=10)
        postal_code_latlong_lst.append(loc)
    except GeocoderTimedOut:
        print("Timeout {}".format(i))
        continue
#------------------------------------------------------

print("Number of postalcode with no lat long: {}".format(len([x for x in postal_code_latlong_lst if x == None])))

#geocode places with no postal codes. RUN ME
key_counter += 1 #for safety
g = initialize_google(key_counter)

street_geocoded = joblib.load("streetgeocoded.pkl")#{}
for i in df2.index:
    if i <= 114217:
        continue
    street = df2["Offence-Street"][i]
    postal_code = df2["Offence-Postal"][i]
    address = df2["Offence-Address"][i]
    if postal_code is None or pd.isnull(postal_code):
        if len(street_geocoded) % 2499 == 0:
            key_counter += 1
            g = initialize_google(key_counter)
        if not pd.isnull(street):
            loc = g.geocode(street.lower() + " Singapore",timeout=10)
        else:
            if not pd.isnull(address):
                loc = g.geocode(address.lower() + " Singapore",timeout=10)
            else:
                loc = None
        street_geocoded[i] = loc
# --------------------------------------------------------

print("Number of addresses with no lat long: {}".format(len([x for x in street_geocoded.values() if x == None])))

postalcode_latlong_mapping = dict(zip(unique_postal_codes,postal_code_latlong_lst))

#map the postal codes to columns
latitude = pd.Series(index = df2.index,dtype=float)
longitude = pd.Series(index = df2.index,dtype=float)

check_index = []
for i in df2.index:
    postal_code = df2["Offence-Postal"][i]
    if postal_code is not None and not pd.isnull(postal_code):
        location = postalcode_latlong_mapping[str(int(postal_code))]
    else:
        location = street_geocoded.get(i)
    if location == None:
        check_index.append(i)
        continue
    latitude.set_value(i,location.latitude)
    longitude.set_value(i,location.longitude)
        
df2["latitide"] = latitude
df2["longitude"] = longitude

from pandas import ExcelWriter
writer = ExcelWriter(wdir+'eems_half_geocoded.xlsx')
df2.to_excel(writer,index=False)
writer.save()

## NOT ENOUGH

key_counter = 0
g = initialize_google(key_counter)

df2 = pd.read_excel("../raw_data/eems_half_geocoded.xlsx")
## Try again for postal code + street
postal_code_dic = {}
df2_null_lat = df2[df2["longitude"].isnull()]
df2_null_lat["Offence-Postal"] = df2_null_lat["Offence-Postal"].map(lambda x:str(int(x)) if not pd.isnull(x) else x)           
unique_postal_codes = get_unique_postal_codes(df2_null_lat)

for i in range(len(unique_postal_codes)):
    code = unique_postal_codes[i]
    street = df2_null_lat[df2_null_lat["Offence-Postal"] == code]["Offence-Street"].head(1).values[0]
    if pd.isnull(code) == False and pd.isnull(street) == False:
        location = g.geocode(street + ' ' + code + ' Singapore')
        postal_code_dic[code] = location

        # if have street and postal code, try.
        # else, if just street, try street
        # if not gg la just drop
# match back to eems data

longCol =  df2["longitude"]
latCol = df2["latitide"]
for i in df2.index:
    postal = df2["Offence-Postal"][i]
    long = df2["longitude"][i]
    if pd.isnull(long):
        if pd.isnull(postal) == False:
            loc = postal_code_dic[str(int(postal))]
            if loc:
                longCol.set_value(i,loc.longitude)
                latCol.set_value(i,loc.latitude)
                
df2["longitude"] = longCol
df2["latitide"] = latCol

## At this point - 392 entries dont have lat long.

def save_file(df2,filename):
    global wdir
    from pandas import ExcelWriter
    writer = ExcelWriter(wdir+filename)
    df2.to_excel(writer,index=False)
    writer.save()

street_dic = {}
for i in df2.index:
    long = df2["longitude"][i]
    if pd.isnull(long):
        street = df2["Offence-Street"][i]
        if not pd.isnull(street) and street not in street_dic:
            loc = g.geocode(street.lower() + ' singapore')
            street_dic[street.lower()] = loc
            
# map it to df
longCol =  df2["longitude"]
latCol = df2["latitide"]
for i in df2.index:
    street = df2["Offence-Street"][i]
    long = df2["longitude"][i]
    if pd.isnull(long):
        if pd.isnull(street) == False:
            loc = street_dic[street.lower()]
            if loc:
                longCol.set_value(i,loc.longitude)
                latCol.set_value(i,loc.latitude)
                
df2["longitude"] = longCol
df2["latitide"] = latCol

## NOT SUCCESSFUL. LAST CHANCE, TRY STREET!

def clean_location(location_string):
    words_to_remove = ["o/p","opp","onto","grass",'patch',"onto","the","ground",
                       "at","the","near","open","field","in","front","pillar","along",
                       "to","l/p","next","outside","of","and","lamp","post","traffic",
                       "exit","taxi","stand","opposite","vicinity","between","beside","under",
                       "drain","pavement","while","sitting","opposite","void","deck",
                       "planted","area","bed"]
    l = location_string.lower().replace('.','').replace('(','').replace(')','').replace(',','')
    l = l.split(' ')
    l = [x for x in l if (x not in words_to_remove) and (x.isdigit() == False)]
    l = ' '.join(l)
    return l
    
location_dic = {}
for i in df2.index:
    long = df2["longitude"][i]
    if pd.isnull(long):
        location = df2["Offence-Location"][i]
        location = clean_location(location)
        if not pd.isnull(street) and location not in location_dic:
            loc = g.geocode(location.lower() + ' singapore',timeout=10)
            location_dic[location.lower()] = loc
            
print(len([x for x in location_dic.values() if x == None])) #142 locations rly cmi


# map it to df
longCol =  df2["longitude"]
latCol = df2["latitide"]
for i in df2.index:
    location = df2["Offence-Location"][i]
    long = df2["longitude"][i]
    if pd.isnull(long):
        if pd.isnull(location) == False:
            loc = location_dic[clean_location(location).lower()]
            if loc:
                longCol.set_value(i,loc.longitude)
                latCol.set_value(i,loc.latitude)
                
df2["longitude"] = longCol
df2["latitide"] = latCol

# At this point, still got 62 rows no lat long.

save_file(df2,'eems_3quarter_geocoded.xlsx')
        
df2 = pd.read_excel(wdir+'eems_3quarter_geocoded_manual.xlsx')
## RUN LINES 259 TO 286 AGAIN

# 19 locations! drop sua LOL
save_file(df2,'eems_mostly_geocoded.xlsx')
df2 = pd.read_excel(wdir+'eems_mostly_geocoded.xlsx')
#final - 4 rows cannot resolve

# EXTRA BECUASE REALIZE SOME GEOCODINGS ARE WRONG.
attempt_counter = 0
loc_counter = 0
key_index = 0
g = initialize_google(key_index)
for i in df2.index:
    if pd.isnull(df2["latitude"][i]):
        location = df2["Offence-Location"][i]
        postal = df2["Offence-Postal"][i]
        if not pd.isnull(location):
            attempt_counter += 1
            if attempt_counter % 2490 == 0:
                key_index += 1
                g = initialize_google(key_index)
            loc = g.geocode(location,region='singapore',timeout=10)
            if loc:
                loc_counter += 1
                df2["latitude"].set_value(i,loc.latitude)
                df2["longitude"].set_value(i,loc.longitude)
                
save_file(df2,"eems_mostly_geocoded2.xlsx")
df2 = pd.read_excel(wdir+"eems_mostly_geocoded2.xlsx")
