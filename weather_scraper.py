#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 08:52:53 2016

@author: waffleboy
"""

import wgetter,os

BASE_URL = "http://weather.gov.sg/files/dailydata/DAILYDATA_{}_{}.csv"
wd = "/home/waffleboy/Desktop/NEA/weather_data"

if not os.path.exists(wd):
    os.mkdir(wd)
    
YEAR_RANGE = [2012,2013,2014,2015,2016]
MONTH_RANGE = list(range(1,13))
MONTH_RANGE = ['0' + str(x) if x < 10 else str(x) for x in MONTH_RANGE]
               
LOCATION_RANGE = {"Jurong West":"S44",
                  "Clementi":"S50"}
                  
                  
for location in LOCATION_RANGE.values():
    for year in YEAR_RANGE:
        for month in MONTH_RANGE:
            duration = year+month
            wgetter.download(BASE_URL.format(location,duration),outdir = wd)
            