#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  3 15:23:02 2017

@author: waffleboy
"""

import pandas as pd
from shapely.geometry import Point,Polygon
from highlighter_googlemaps import show_on_google_maps
import json

# one time for speed
# REQUIRE THESE FILES TO WORK. Each line corresponds to one dataset
filepath_dic = {"enforcement":pd.read_excel("../raw_data/eems_mostly_geocoded2.xlsx"),
     "feedback":pd.read_excel("../raw_data/feedback_geocoded_extra_cols_and_smoking_emoved.xlsx"),
     "cleaning":pd.read_excel("../raw_data/cleaning_regeocoded.xlsx")
     }


# Load singapore polygon
with open("../admin_level_2.geojson",'r',encoding="utf-8") as f:
    b = json.loads(f.read())
borderpolygon = Polygon(b['features'][0]['geometry']['coordinates'][1][0])

SINGAPORE_LONGITUDE = 42 #in km
SINGAPORE_LATITUDE = 29.5
DESIRED_RESOLUTION = (0.5,1) #0.5km by 1km

SINGAPORE_MIN_LONG = 103.6034
SINGAPORE_MAX_LONG = 104.039
SINGAPORE_MIN_LAT = 1.23081
SINGAPORE_MAX_LAT = 1.464216

total_area = SINGAPORE_LONGITUDE*SINGAPORE_LATITUDE
box_area = DESIRED_RESOLUTION[0]*DESIRED_RESOLUTION[1]

## insert box fixing methods here.
def calculate_num_boxes(total_area,box_area):
    return int(total_area/box_area)

num_boxes = calculate_num_boxes(total_area,box_area)

# maps to number of cleaning per day
# hoourly - 12
def cleaning_schedule_mapper(entry):
    if entry == '3x/week':
        return 3 / (24*7)
    if entry == 'daily':
        return 1
    if entry == 'hourly':
        return 12
    if entry == 'alternate_day':
        return 1/2
    if entry == "weekly":
        return 1/(24*7)
    if entry == "3x/day":
        return 3
    if entry == "2x/day":
        return 2
    if entry == "2x/week":
        return 2/(24*7)
    return

high_cleaning = ['daily',"hourly","3x/day","2x/day"]

def box_in_singapore(box):
    global borderpolygon
    point = Point(box.bottom_right[1],box.bottom_right[0])
    point2 = Point(box.top_right[1],box.top_right[0])
    if borderpolygon.contains(point) and borderpolygon.contains(point2):
        return True
    return False
    
## Main Box Class. It will contain every smaller box inside as well.
class Box(object):
    master_enforcement_count = []
    master_feedback_count = []
    all_boxes = []
    
    def __init__(self,bottom_left,top_right):
        self.top_right = top_right
        self.top_left = (top_right[0],bottom_left[1])
        self.bottom_left = bottom_left
        self.bottom_right = (bottom_left[0],top_right[1])
        self.max_lat = self.set_max_lat()
        self.min_lat = self.set_min_lat()
        self.max_long = self.set_max_long()
        self.min_long = self.set_min_long()
        self.cleaning_schedule = {}
        self.cleaning_addresses = []
        self.cleaning_statistics = None
        self.cleaning_schedule_overview = ''
        self.enforcement_count = 0
        self.feedback_count = 0
        self.enforcement_index = -1
        self.feedback_index = -1
        self.count = len(Box.all_boxes)
        Box.all_boxes.append(self)
    
    #TODO: Refactor entire class.
    @staticmethod #SUPER HACKY - assumes enforcement will always be there.
    def conditional_query(enforcement,feedback,cleaning):
        temp = []
        if enforcement["condition"] == "low":
            temp = [box for box in Box.all_boxes if box.enforcement_count <= enforcement["value"]]
        else:
            temp = [box for box in Box.all_boxes if box.enforcement_count >= enforcement["value"]]
        
        if feedback:
            if feedback["condition"] == "low":
                temp = [box for box in temp if box.feedback_count <= feedback["value"]]
            elif feedback["condition"] == "high":
                temp = [box for box in temp if box.feedback_count >= feedback["value"]]
        
        if cleaning:
            if cleaning["condition"] == "low":
                temp = [box for box in temp if box.cleaning_schedule_overview == "LOW"]
            elif cleaning["condition"] == "high":
                temp = [box for box in temp if box.cleaning_schedule_overview == "HIGH"]
            
        if temp:
            temp = [box for box in temp if box_in_singapore(box)]
        return temp
    
    @staticmethod
    def get_summary_statistics():
        print("Of all {} boxes currently in memory:".format(len(Box.all_boxes)))
        summary_stats_enforcement = pd.Series(Box.master_enforcement_count).describe()
        summary_stats_feedback = pd.Series(Box.master_feedback_count).describe()
        print("Enforcement:")
        print(summary_stats_enforcement)
        print("Feedback:")
        print(summary_stats_feedback)
        return
    
    @staticmethod
    def reset_box():
        Box.all_boxes = []
    
    @staticmethod
    def calculate_stats(data):
        if data == "enforcement":
            stats = [box.enforcement_count for box in Box.all_boxes]
        elif data == "feedback":
            stats = [box.feedback_count for box in Box.all_boxes]
        else:
            return
        return pd.Series(stats).describe()
        
    def is_coordinate_in_box(self,lat,long):
        if lat < self.max_lat and lat >= self.min_lat:
            if long < self.max_long and long >= self.min_long:
                return True
        return False

    def set_max_lat(self):
        return self.top_right[0]
        
    def set_min_lat(self):
        return self.bottom_left[0]
        
    def set_max_long(self):
        return self.top_right[1]
        
    
    def set_min_long(self):
        return self.bottom_left[1]
        
    def add_cleaning_schedule(self,schedule):
        if schedule not in self.cleaning_schedule:
            self.cleaning_schedule[schedule] = 1
        else:
            self.cleaning_schedule[schedule] += 1
        
    def calculate_cleaning_overview(self):
        high = 0
        low = 0 #this is seriously bad coding.
        for key,value in self.cleaning_schedule.items():
            if key in high_cleaning:
                high += value
            else:
                low += value
        self.cleaning_statistics = (low,high)
        if high == 0 and low == 0:
            self.cleaning_schedule_overview = "NONE"
            return
            
        if high > low:
            self.cleaning_schedule_overview = "HIGH"
        else:
            self.cleaning_schedule_overview = "LOW"
    
    def add_cleaning_address(self,add):
        self.cleaning_addresses.append(add)
        
    def increment_enforcement_count(self):
        if self.enforcement_index == -1: #if ive never been assigned
            Box.master_enforcement_count.append(1) #curr value
            self.enforcement_index  = len(Box.master_enforcement_count) - 1
        else:
             Box.master_enforcement_count[self.enforcement_index] += 1
        self.enforcement_count += 1
        
    def increment_feedback_count(self):
        if self.feedback_index == -1: #if ive never been assigned
            Box.master_feedback_count.append(1) #curr value
            self.feedback_index  = len(Box.master_feedback_count) - 1
        else:
             Box.master_feedback_count[self.feedback_index] += 1
        self.feedback_count += 1
        
def initialize_master_array():
    global SINGAPORE_LONGITUDE,SINGAPORE_LATITUDE,DESIRED_RESOLUTION
    master_array = []
    number_of_lat_boxes = int(SINGAPORE_LATITUDE / DESIRED_RESOLUTION[0])
    number_of_long_boxes = int(SINGAPORE_LONGITUDE / DESIRED_RESOLUTION[1])
    
    print("Lat boxes by Long boxes: {}x{}".format(number_of_lat_boxes,number_of_long_boxes))
    
    increment_lat = (SINGAPORE_MAX_LAT - SINGAPORE_MIN_LAT) / number_of_lat_boxes
    increment_long = (SINGAPORE_MAX_LONG - SINGAPORE_MIN_LONG) / number_of_long_boxes
    
    current_top_right_lat = SINGAPORE_MAX_LAT
    current_top_right_long = SINGAPORE_MIN_LONG + increment_long
    current_bottom_left_lat = SINGAPORE_MAX_LAT - increment_lat
    current_bottom_left_long = SINGAPORE_MIN_LONG
    
    for i in range((number_of_lat_boxes)):
        temp_array = []
        for j in range((number_of_long_boxes)):
            btm_left = (current_bottom_left_lat,current_bottom_left_long)
            top_right = (current_top_right_lat,current_top_right_long)
            temp_array.append(Box(btm_left,top_right))
            current_top_right_long += increment_long
            current_bottom_left_long += increment_long
        master_array.append(temp_array)
        current_bottom_left_long = SINGAPORE_MIN_LONG
        current_top_right_long = SINGAPORE_MIN_LONG + increment_long
        current_bottom_left_lat -= increment_lat
        current_top_right_lat -= increment_lat
    return master_array
#    
#master_array = initialize_master_array()
#print("Dividing Singapore into {} squares.".format(num_boxes))


#wdir = "/home/waffleboy/Desktop/NEA/"
#print("Loading data into memory..")
#enforcement = pd.read_excel(wdir+"raw_data/eems_mostly_geocoded2.xlsx")
#feedback = pd.read_excel(wdir+"raw_data/feedback_combined_latlong.xlsx")
#cleaning = pd.read_excel("../pdf2docx/combined_cleaning_schedule_FINAL_geocoded.xlsx")

# load cleaning
def load_into_master_array(master_array,data_type,df):
    for i in df.index:
        if not pd.isnull(df["latitude"][i]):
            lat = df["latitude"][i]
            long = df["longitude"][i]
            for long_box in master_array:
                for box in long_box:
                    if box.is_coordinate_in_box(lat,long):
                        if data_type == "enforcement":
                            box.increment_enforcement_count()
                        elif data_type == "feedback":
                            box.increment_feedback_count()
                        elif data_type == "cleaning":
                            box.add_cleaning_schedule(df["frequency"][i])
                            box.add_cleaning_address(df["location"][i])
                        else:
                            raise Exception("Sorry - unsupported data_type given")
    for row in master_array:
        for box in row:
            box.calculate_cleaning_overview()
            
    return master_array
#
#print("Populating squares with data..")
#print("Loading enforcement data..")
#master_array = load_into_master_array(master_array,"enforcement",enforcement)
#print("Loading feedback data..")
#master_array = load_into_master_array(master_array,"feedback",feedback)
#print("Loading cleaning data..")
#master_array = load_into_master_array(master_array,"cleaning",cleaning)
#
#summary_stats_enforcement = pd.Series(Box.master_enforcement_count).describe()
#summary_stats_feedback = pd.Series(Box.master_feedback_count).describe()
#
#upper_quartile_enf = summary_stats_enforcement["75%"]
#median_enf = summary_stats_enforcement["50%"]
#lower_quartile_enf = summary_stats_enforcement["25%"]
#
#upper_quartile_feed = summary_stats_feedback["75%"]
#median_feed = summary_stats_feedback["50%"]
#lower_quartile_feed = summary_stats_feedback["25%"]


def get_predefined_groups(master_array,upper_quartile_enf,lower_quartile_enf,\
                          upper_quartile_feed,lower_quartile_feed):
    print("Getting predefined groups for enforcement and feedback only: ")
    print("Using Enf Upper/Lower cutoff: {}/{}" .format(upper_quartile_enf,lower_quartile_enf))
    print("Using Feedback Upper/Lower cutoff: {},{}".format(upper_quartile_feed,lower_quartile_feed))
    #Enforcement, feedback, cleaning
    master_dic = {"highE_highF":[],
                  "highE_lowF":[],
                  "lowE_highF":[],
                  "lowE_lowF":[]
                  }
    
    for row in master_array:
        for box in row:
            if box.enforcement_count >= upper_quartile_enf and box.feedback_count >=upper_quartile_feed:
                master_dic["highE_highF"].append(box)
            
            elif box.enforcement_count >= upper_quartile_enf and box.feedback_count <= lower_quartile_feed:
                master_dic["highE_lowF"].append(box)
            
            elif box.enforcement_count <= lower_quartile_enf and box.feedback_count >= upper_quartile_feed:
                master_dic["lowE_highF"].append(box)
                
            elif box.enforcement_count <= lower_quartile_enf and box.feedback_count <= lower_quartile_feed:
                master_dic["lowE_lowF"].append(box)
                
    return master_dic

def get_predefined_groups2(upper_quartile_enf,lower_quartile_enf,\
                          upper_quartile_feed,lower_quartile_feed):
    print("Getting predefined groups for all 3 datasets: ")
    print("Using Enf Upper/Lower cutoff: {}/{}" .format(upper_quartile_enf,lower_quartile_enf))
    print("Using Feedback Upper/Lower cutoff: {},{}".format(upper_quartile_feed,lower_quartile_feed))
    master_dic = {}
                  
    master_dic["highE_highF_highC"] = Box.conditional_query({"condition":"high",
                                                            "value":upper_quartile_enf},
                                                            {"condition":"high",
                                                             "value":upper_quartile_feed},
                                                             {"condition":"high"})
    
    master_dic["highE_lowF_highC"] = Box.conditional_query({"condition":"high",
                                                            "value":upper_quartile_enf},
                                                            {"condition":"low",
                                                             "value":lower_quartile_feed},
                                                             {"condition":"high"})
    
    master_dic["lowE_highF_highC"] = Box.conditional_query({"condition":"low",
                                                            "value":lower_quartile_enf},
                                                            {"condition":"high",
                                                             "value":upper_quartile_feed},
                                                             {"condition":"high"})
    
    master_dic["lowE_lowF_highC"] = Box.conditional_query({"condition":"low",
                                                            "value":lower_quartile_enf},
                                                            {"condition":"low",
                                                             "value":lower_quartile_feed},
                                                             {"condition":"high"})
    
    return master_dic
    
    
def get_group_statistics(master_dic):
    for key,value in master_dic.items():
        print("Group {} has {} boxes".format(key,len(value)))

def subset_df_on_date_range(df,dataname,begin_date,end_date):
    if dataname == "enforcement":
        column = "Offence-Date"
    else:
        column = "Created Date"
    mask = (df[column] >= begin_date) & (df[column] <= end_date)
    return df.loc[mask]
    
#==============================================================================
#               Master functions to generate alot of maps
#==============================================================================
def generate_filename(groupname,median,cleaning_included,date_begin,date_end):
    file = ''
    if date_begin:
        file += str(date_begin.year) +'_'
        file += str(date_end.year) + '_'
    else:
        file += "2_year_"
    file += 'median_' if median else 'quartile_'
    
    if not cleaning_included:
        file += "NO_cleaning_"
    file += groupname
    return file
    
def master_run_function(df_dic,save_to_file=True,median=True,cleaning_included=True,\
                        date_begin=None,date_end=None):
    master_array = initialize_master_array()
    for dataname,df in filepath_dic.items():
        missing = sum(df["latitude"].isnull())
        if missing:
            print("{} missing values found in {}, removing.".format(missing,dataname))
            df = df[~df["latitude"].isnull()]
        if date_begin and dataname != "cleaning":
            df = subset_df_on_date_range(df,dataname,date_begin,date_end)
        print("Loading into master array")
        master_array = load_into_master_array(master_array,dataname,df)
        
    summary_stats_enforcement = pd.Series(Box.master_enforcement_count).describe()
    summary_stats_feedback = pd.Series(Box.master_feedback_count).describe()
    print("Enforcement Summary:")
    print(summary_stats_enforcement)
    print("Feedback Summary:")
    print(summary_stats_feedback)
#    summary_stats_enforcement = Box.calculate_stats("enforcement")
#    summary_stats_feedback = Box.calculate_stats("feedback")
    
    upper_quartile_enf = summary_stats_enforcement["75%"]
    median_enf = summary_stats_enforcement["50%"]
    lower_quartile_enf = summary_stats_enforcement["25%"]
    
    upper_quartile_feed = summary_stats_feedback["75%"]
    median_feed = summary_stats_feedback["50%"]
    lower_quartile_feed = summary_stats_feedback["25%"]
    
    if cleaning_included:
        if median:
            print("Using median:")
            group_dic_2 = get_predefined_groups2(median_enf,median_enf,median_feed,median_feed)
        else:
            group_dic_2 = get_predefined_groups2(upper_quartile_enf,lower_quartile_enf,upper_quartile_feed,lower_quartile_feed)
    else:
        if median:
            print("Using median:")
            group_dic_2 = get_predefined_groups(median_enf,median_enf,median_feed,median_feed)
        else:
            group_dic_2 = get_predefined_groups(upper_quartile_enf,lower_quartile_enf,upper_quartile_feed,lower_quartile_feed)
    
    if not save_to_file:
        return group_dic_2
        
    for groupname,boxes in group_dic_2.items():
        filename = generate_filename(groupname,median,cleaning_included,date_begin,date_end)
        show_on_google_maps(boxes,"../identifier_base.html","../raw_data/final/{}.html".format(filename))
        # defined in another file, highlighter_googlemaps.py. im so sorry to my future self
    Box.reset_box() #remove entries inside
    return
#    
#
#    
#print("Calculating predefined groups..")
#group_dic = get_predefined_groups(master_array,median_enf,median_enf,median_feed,median_feed)
#get_group_statistics(group_dic)
#
#group_dic_2 = get_predefined_groups2(median_enf,median_enf,median_feed,median_feed)
#get_group_statistics(group_dic_2)

#create 2 year maps
master_run_function(filepath_dic)
import datetime
#create 2015-16 maps, median
master_run_function(filepath_dic,cleaning_included=True,date_begin = datetime.date(2015,11,30),date_end=datetime.date(2016,11,30))
#create 2014-15 maps, median
master_run_function(filepath_dic,cleaning_included=True,date_begin = datetime.date(2014,11,30),date_end=datetime.date(2015,11,30))


#
#show_on_google_maps(group_dic_2["lowE_lowF_highC"],"../identifier_base.html","../raw_data/2_year_median_lowlowhigh.html")
#show_on_google_maps(group_dic_2["highE_highF_highC"],"../identifier_base.html","../raw_data/2_year_median_highhighhigh.html")
#show_on_google_maps(group_dic_2["lowE_highF_highC"],"../identifier_base.html","../raw_data/2_year_median_lowhighhigh.html")
