#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 14:28:08 2016

@author: waffleboy
"""

# CONTAINS BOTH CIRCLE AND HEATMAP CAUSE SIMILAR CODE.

import pandas as pd
from copy import deepcopy
import os
import datetime
import calendar
from pandas import ExcelWriter


wdir = "/home/waffleboy/Desktop/NEA/"
BASE_HEATMAP_LOCATION = "../heatmap_base.html"
BASE_CIRCLE_LOACTION = "../circle_base.html"
        
CIRCLE_INNER_TEMPLATE = {'properties': {}, 'geometry': {'coordinates': [], 'type': 'Point'}, 
                      'type': 'Feature'}

## helper to make it easier for different combinations
def subset_df_on_date_range(df,column_name,begin_date,end_date):
    mask = (df[column_name] >= begin_date) & (df[column_name] <= end_date)
    return df.loc[mask]

# assumes dataframe has latitude longitude columns
def convert_latlong_to_heatmap_format(df):
    df = remove_missing_values(df)
    lat = df["latitude"]
    long = df["longitude"]
    base_string = "new google.maps.LatLng({},{}),"
    
    building_string = ''
    for i in df.index:
        building_string += base_string.format(lat[i],long[i])
        
    building_string = building_string[:-1] # remove last comma
    return building_string

def convert_latlong_to_circle_format(df,cleaning=False):
    global CIRCLE_INNER_TEMPLATE
    CIRCLE_BASE = {'features': [], 
        'type': 'FeatureCollection'}
    df = remove_missing_values(df)
    lat = df["latitude"]
    long = df["longitude"]
    for i in df.index:
        curr_lat = lat[i]
        curr_long = long[i]
        temp_copy = deepcopy(CIRCLE_INNER_TEMPLATE)
        temp_copy["geometry"]["coordinates"] = [curr_long,curr_lat] #reversed
        if cleaning:
            temp_copy["properties"]["group"] = df["frequency"][i]
        CIRCLE_BASE["features"].append(temp_copy)
    return CIRCLE_BASE

def remove_missing_values(df):
    df = df[~df["latitude"].isnull()]
    return df

# hacky join function because .format doesnt work with multiple braces
def replace_with_latlong(heatmap,building_string):
    word = "REPLACE_ME"
    skip_length = len(word)
    idx = heatmap.find(word)
    if type(building_string) == dict:
        building_string = str(building_string) #hack
        
    heatmap = heatmap[:idx] + building_string + heatmap[idx+skip_length:]
    return heatmap
    
def build_heatmap(df):
    global BASE_HEATMAP_LOCATION
    building_string = convert_latlong_to_heatmap_format(df)
    with open(BASE_HEATMAP_LOCATION,'r') as f:
        heatmap = f.read()
    heatmap = replace_with_latlong(heatmap,building_string)
    return heatmap

def build_circlemap(df,cleaning):
    building_string = convert_latlong_to_circle_format(df,cleaning)
    with open(BASE_CIRCLE_LOACTION,'r') as f:
        circlemap = f.read()
    circlemap = replace_with_latlong(circlemap,building_string)
    return circlemap
    
def save_map(mapname,filename):
    with open(filename,'w') as f:
        f.write(mapname)
    return
    
def create_and_save_heatmap(df,save_to_filepath):
    heatmap = build_heatmap(df)
    save_map(heatmap,save_to_filepath)
    
def create_and_save_circlemap(df,save_to_filepath,cleaning):
    circlemap = build_circlemap(df,cleaning)
    save_map(circlemap,save_to_filepath)
    
#==============================================================================
#                           MAIN FUNCTIONs
#==============================================================================
def load_df_and_create_heatmap(excel_filepath,save_to_filepath):
    df = pd.read_excel(excel_filepath)
    create_and_save_heatmap(df,save_to_filepath)
    
    
def load_df_and_create_circlemap(excel_filepath,save_to_filepath,cleaning=False):
    df = pd.read_excel(excel_filepath)
    create_and_save_circlemap(df,save_to_filepath,cleaning)
    
    
def load_df_and_create_combined_map(enforcement_path,feedback_path, \
                                    cleaning_path,save_to_filepath,cleaning_high_only):
    global BASE_HEATMAP_LOCATION, BASE_CIRCLE_LOACTION
    BASE_CIRCLE_LOACTION = "../combined_heatmap_base.html"
    enf = pd.read_excel(enforcement_path)
    feed = pd.read_excel(feedback_path)
    clean = pd.read_excel(cleaning_path)
    
    if cleaning_high_only:
        high_cleaning = ['daily',"hourly","3x/day","2x/day"]
        clean = clean[clean["frequency"].isin(high_cleaning)]
    
    create_and_save_circlemap(clean,save_to_filepath,True)
    BASE_HEATMAP_LOCATION = save_to_filepath
    create_and_save_heatmap(enf,save_to_filepath)
    create_and_save_heatmap(feed,save_to_filepath)
    BASE_HEATMAP_LOCATION = "../heatmap_base.html"
    BASE_CIRCLE_LOACTION = "../circle_base.html"

def save_df(df,filename):
    global wdir
    writer = ExcelWriter(wdir+'raw_data/{}.xlsx'.format(filename))
    df.to_excel(writer,index=False)
    writer.save()
    
#==============================================================================
#                           Monthly Timeseries
#==============================================================================
def generate_monthly_heatmap_timeseries(df,date_column_name,date_begin,date_end,wdir):
    number_of_months = calculate_number_of_months(date_begin,date_end)
    print("Beginning timeseries generation for {} months".format(number_of_months))
    current_date = date_begin
    next_month = get_next_month(current_date)
    if not os.path.exists(wdir):
        os.mkdir(wdir)
    df = remove_missing_values(df)
    df[date_column_name] = pd.to_datetime(df[date_column_name])
    counter = 1
    for i in range(number_of_months):
        subset_df = subset_df_on_date_range(df,date_column_name,current_date,next_month)
        print("Doing {} {} - {} points".format(\
              calendar.month_name[current_date.month],current_date.year,len(subset_df)))
        filepath = generate_monthly_heatmap_filepath(counter,current_date.month,current_date.year,\
                                                     wdir)
        create_and_save_heatmap(subset_df,filepath)
        current_date = next_month
        next_month = get_next_month(current_date)
        counter += 1
    return
    
def get_next_month(curr_date):
    if curr_date.month < 12:
        curr_date = curr_date.replace(month = curr_date.month + 1)
        return curr_date
    return curr_date.replace(month = 1,year = curr_date.year + 1)
    
def calculate_number_of_months(date_begin,date_end):
    if date_end.year == date_begin.year:
        return date_end.month - date_begin.month
    return (date_end.year - date_begin.year) * 12 + (date_end.month - date_begin.month)
    
def generate_monthly_heatmap_filepath(counter,month,year,wdir):
    return wdir + str(counter) +'_'+ calendar.month_name[month] +'_'+ str(year) + '.html'
#==============================================================================
# 
#==============================================================================

## Create EEMS Heatmap - 2 years
load_df_and_create_heatmap(wdir+"raw_data/eems_mostly_geocoded2.xlsx",wdir+"raw_data/final/2_year_EEMS_Heatmap.html")
# EEMS CIRCLEAP
#load_df_and_create_circlemap(wdir+"raw_data/eems_mostly_geocoded2.xlsx",wdir+"raw_data/EEMS_circlemap.html",cleaning=False)

## Create iCare feedback Heatmap - 2 years
load_df_and_create_heatmap(wdir+"raw_data/feedback_geocoded_extra_cols_and_smoking_emoved.xlsx",wdir+"raw_data/final/2_year_icare_Heatmap.html")

## Trial cleaning schedule
#load_df_and_create_circlemap(wdir+"pdf2docx/combined_cleaning_schedule_FINAL_geocoded.xlsx",wdir+"raw_data/cleaning_schedule_Circlemap_nobusstop.html",cleaning=True)



#1 year data - LEGACY MIXED CODE. IM SORRY FUTURE SELF
df = pd.read_excel(wdir+"raw_data/eems_mostly_geocoded2.xlsx")
df2 = subset_df_on_date_range(df,"Offence-Date",datetime.date(2014,12,1),datetime.date(2015,11,30))
create_and_save_heatmap(df2,wdir+"raw_data/final/2014_2015_EEMS_heatmap.html")

df = subset_df_on_date_range(df,"Offence-Date",datetime.date(2015,12,1),datetime.date(2016,11,30))
save_df(df,'2015_2016_eems.xlsx')

df = pd.read_excel(wdir+"raw_data/feedback_geocoded_extra_cols_and_smoking_emoved.xlsx")
df2 = subset_df_on_date_range(df,"Created Date",datetime.date(2014,12,1),datetime.date(2015,11,30))
create_and_save_heatmap(df2,wdir+"raw_data/final/2014_2015_icare_Heatmap.html")

df = subset_df_on_date_range(df,"Created Date",datetime.date(2015,12,1),datetime.date(2016,11,30))
save_df(df,'2015_2016_feedback.xlsx')

#legacy code
load_df_and_create_circlemap(wdir+"raw_data/2015_2016_eems.xlsx",wdir+"raw_data/final/2015_2016_EEMS_circlemap.html",cleaning=False)
load_df_and_create_heatmap(wdir+"raw_data/2015_2016_feedback.xlsx",wdir+"raw_data/final/2015_2016_1_year_icare_Heatmap.html")
load_df_and_create_heatmap(wdir+"raw_data/2015_2016_eems.xlsx",wdir+"raw_data/final/2015_2016_EEMS_heatmap.html")




load_df_and_create_combined_map(wdir+"raw_data/eems_mostly_geocoded2.xlsx",\
                                wdir+"raw_data/feedback_combined_latlong.xlsx",\
                                wdir+"raw_data/cleaning_schedule_final_geocoded.xlsx",\
                                "../raw_data/final/2_year_combined.html",cleaning_high_only=True)


## TIMESERIES GENERATION
df = pd.read_excel(wdir+"raw_data/eems_mostly_geocoded2.xlsx")
generate_monthly_heatmap_timeseries(df,"Offence-Date",datetime.date(2014,12,1),
                                    datetime.date(2016,12,1),\
                                    "../raw_data/final/timeseries/enforcement/")

df = pd.read_excel(wdir+"raw_data/feedback_geocoded_extra_cols_and_smoking_emoved.xlsx")
generate_monthly_heatmap_timeseries(df,"Created Date",datetime.date(2014,12,1),
                                    datetime.date(2016,12,1),\
                                    "../raw_data/final/timeseries/feedback/")
#==============================================================================
# ## Random
#==============================================================================

def verify_if_within_singapore(lat,long):
    if lat > 1.22 and lat <= 1.47:
        if long > 103.6 and long <= 105.04:
            return True
    return False

def remove_latlong_if_not_in_sg(df):
    counter = 0
    for i in df.index:
        lat = df["latitude"][i]
        long = df["longitude"][i]
        if pd.isnull(lat):
            continue
        if not verify_if_within_singapore(lat,long):
            counter += 1
            df["latitude"].set_value(i,None)
            df["longitude"].set_value(i,None)
    print(" {} Entries removed - Not in singapore".format(counter))
    return df


#excel_filepath = wdir+"pdf2docx/combined_cleaning_schedule_round4_geocoded.xlsx"
#df = pd.read_excel(excel_filepath)
#
#df = remove_latlong_if_not_in_sg(df)
#
#
#
#from pandas import ExcelWriter
#writer = ExcelWriter(excel_filepath)
#df.to_excel(writer,index=False)
#writer.save()