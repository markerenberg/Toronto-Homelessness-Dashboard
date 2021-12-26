# ======== Scrape site for data ======== #

#import imports

import os
import time
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly
from datetime import datetime
import time

# Get data files
#local_path = r'C:\Users\marke\Downloads\Datasets\Toronto_Homelessness'
local_path = r'/Users/merenberg/Documents/Precision'
sna_export = pd.read_csv(local_path+r'\sna2018opendata_export.csv').fillna(0)
sna_rows = pd.read_csv(local_path+r'\sna2018opendata_keyrows.csv')
sna_cols = pd.read_csv(local_path+r'\sna2018opendata_keycolumns.csv')
shelter_flow = pd.read_csv(local_path+r'\toronto-shelter-system-flow_march4.csv')
occupancy_curr = pd.read_csv(local_path+r'\Daily_shelter_occupancy_current.csv')
occupancy_2020 = pd.read_csv(local_path+r'\daily-shelter-occupancy-2020.csv')

summary_metrics = pd.read_csv(local_path+r'/summary_metric_changes.csv')

################### Street Needs Assessment ###################
sna_export = sna_export.merge(sna_rows.iloc[:,:3],on='SNA RESPONSE CATEGORY')

# Pivot on question-response
q_cols = ['SNA RESPONSE CATEGORY','QUESTION/CATEGORY DESCRIPTION','RESPONSE']
shelter_cols = ['OUTDOORS','CITY-ADMINISTERED SHELTERS','24-HR RESPITE','VAW SHELTERS']
dem_cols = ['SINGLE ADULTS','FAMILY','YOUTH']

sna_melt = sna_export.melt(id_vars=q_cols,value_vars=shelter_cols+dem_cols+['TOTAL'],
                           var_name='GROUP',value_name='COUNT')

# Track count/average responses
avg_cols = [cat for cat in sna_melt['SNA RESPONSE CATEGORY'].unique() if ('AVERAGE' in cat)]
cnt_cols = [cat for cat in sna_melt['SNA RESPONSE CATEGORY'].unique() if ('COUNT' in cat)]

# Plot bar graph of question-response
q1 = sna_export[sna_export['QUESTION/CATEGORY DESCRIPTION']=='What family members are staying with you tonight?']
fig = px.bar(q1, x="RESPONSE", y=shelter_cols, title='What family members are staying with you tonight?')
fig.show()

q1 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION']=='What family members are staying with you tonight?')\
    &(~sna_melt['SNA RESPONSE CATEGORY'].isin(cnt_cols))\
    &(sna_melt['GROUP'].isin(shelter_cols))]
q1_bar = px.bar(q1.loc[q1['GROUP'].isin(shelter_cols),], x="RESPONSE", y="COUNT", color="GROUP", title="What family members are staying with you tonight?")
#fig.show()
#plotly.offline.plot(q1_bar)

# Question 7: Have you stayed in an emergency shelter in the past 12 months?
q7 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION']=="Have you stayed in an emergency shelter in the past 12 months?")\
                   &(~sna_melt['RESPONSE'].isin(["Don’t know","Decline to answer"]))\
                   &(sna_melt['RESPONSE'].notnull()),]

q7_bar = px.bar(q7.loc[q7['GROUP'].isin(shelter_cols),],\
                 x="RESPONSE", y="COUNT", color="GROUP", \
                 title="Have you stayed in an emergency shelter in the past 12 months?",\
                 text='COUNT')
#plotly.offline.plot(q7_bar)

# Question 22: What would help you find housing?
q22 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION']=="Please tell me which ones would help you personally find housing.")\
                   &(~sna_melt['RESPONSE'].isin(["Don't know","Decline to answer"]))\
                   &(sna_melt['RESPONSE'].notnull()),]

q22_bar = px.bar(q22.loc[q22['GROUP'].isin(shelter_cols),],\
                 x="RESPONSE", y="COUNT", color="GROUP", \
                 title="What would help you personally find housing?",\
                 text='COUNT')
#plotly.offline.plot(q22_bar)

# Question 23: In the past 6 months, have you
q23 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION'].str.contains("In the past 6 months, have you"))\
                   &(sna_melt['RESPONSE']=='Yes'),].drop("RESPONSE",axis=1)
q23['RESPONSE'] = q23['QUESTION/CATEGORY DESCRIPTION'].str[32:]

q23_bar = px.bar(q23.loc[q23['GROUP'].isin(shelter_cols),],\
                 x="RESPONSE", y="COUNT", color="GROUP", \
                 title="In the past 6 months, you have:",\
                 text='COUNT')
#plotly.offline.plot(q23_bar)

################### Summary Metrics ###################

# COVERAGE
coverage = summary_metrics.loc[summary_metrics['METRIC']=='COVERAGE',]
cov_bar = go.Figure(data=[
    go.Bar(name='NEW TRAIN',
           x=coverage.loc[coverage['FRAMEWORK']=='NEW TRAIN','PARTNER'],
           y=coverage.loc[coverage['FRAMEWORK']=='NEW TRAIN','VALUE'],
           text=coverage.loc[coverage['FRAMEWORK']=='NEW TRAIN','VALUE'].round(3),
           textposition='auto'),
    go.Bar(name='NEW OOT',
           x=coverage.loc[coverage['FRAMEWORK'] == 'NEW OOT', 'PARTNER'],
           y=coverage.loc[coverage['FRAMEWORK'] == 'NEW OOT', 'VALUE'],
           text=coverage.loc[coverage['FRAMEWORK']=='NEW OOT','VALUE'].round(3),
           textposition='auto'),
    go.Bar(name='OLD',
           x=coverage.loc[coverage['FRAMEWORK']=='OLD','PARTNER'],
           y=coverage.loc[coverage['FRAMEWORK']=='OLD','VALUE'],
           text=coverage.loc[coverage['FRAMEWORK']=='OLD','VALUE'].round(3),
           textposition='auto')
])
cov_bar.update_yaxes(title='Coverage')
cov_bar.update_layout(barmode='group',
                      title_text='Coverage Metrics By Partner & Framework',
                      title_x=0.5,
                      font=dict(size=24)
                      )
#plotly.offline.plot(cov_bar)

# ACCURACY
accuracy = summary_metrics.loc[summary_metrics['METRIC']=='ACCURACY',]
acc_bar = go.Figure(data=[
    go.Bar(name='NEW TRAIN',
           x=accuracy.loc[accuracy['FRAMEWORK']=='NEW TRAIN','PARTNER'],
           y=accuracy.loc[accuracy['FRAMEWORK']=='NEW TRAIN','VALUE'],
           text=accuracy.loc[accuracy['FRAMEWORK']=='NEW TRAIN','VALUE'].round(3),
           textposition='auto'),
    go.Bar(name='NEW OOT',
           x=accuracy.loc[accuracy['FRAMEWORK'] == 'NEW OOT', 'PARTNER'],
           y=accuracy.loc[accuracy['FRAMEWORK'] == 'NEW OOT', 'VALUE'],
           text=accuracy.loc[accuracy['FRAMEWORK']=='NEW OOT','VALUE'].round(3),
           textposition='auto'),
    go.Bar(name='OLD',
           x=accuracy.loc[accuracy['FRAMEWORK']=='OLD','PARTNER'],
           y=accuracy.loc[accuracy['FRAMEWORK']=='OLD','VALUE'],
           text=accuracy.loc[accuracy['FRAMEWORK']=='OLD','VALUE'].round(3),
           textposition='auto')
])
acc_bar.update_yaxes(title='Accuracy')
acc_bar.update_layout(barmode='group',
                      title_text='Accuracy Metrics By Partner & Framework',
                      title_x=0.5,
                      font=dict(size=24)
                      )
#plotly.offline.plot(acc_bar)

# TRAIN TIME
time = summary_metrics.loc[summary_metrics['METRIC']=='TRAIN TIME',]
time_bar = go.Figure(data=[
    go.Bar(name='NEW TRAIN',
           x=time.loc[time['FRAMEWORK']=='NEW TRAIN','PARTNER'],
           y=time.loc[time['FRAMEWORK']=='NEW TRAIN','VALUE'],
           text=time.loc[time['FRAMEWORK']=='NEW TRAIN','VALUE'].round(3),
           textposition='auto'),
    go.Bar(name='NEW OOT',
           x=time.loc[time['FRAMEWORK'] == 'NEW OOT', 'PARTNER'],
           y=time.loc[time['FRAMEWORK'] == 'NEW OOT', 'VALUE'],
           text=time.loc[time['FRAMEWORK']=='NEW OOT','VALUE'].round(3),
           textposition='auto'),
    go.Bar(name='OLD',
           x=time.loc[time['FRAMEWORK']=='OLD','PARTNER'],
           y=time.loc[time['FRAMEWORK']=='OLD','VALUE'],
           text=time.loc[time['FRAMEWORK']=='OLD','VALUE'].round(3),
           textposition='auto')
])
time_bar.update_yaxes(title='Time (minutes)')
time_bar.update_layout(barmode='group',
                      title_text='Train Time (Minutes) By Partner/Framework',
                      title_x=0.5,
                      font=dict(size=24)
                      )
#plotly.offline.plot(time_bar)

################### Daily Shelter Occupancy ###################

# Read in csv
root_path = r'/Users/markerenberg/Documents/Github/homelessness-dash/homelessness-dash/'
data_path = root_path + "underlying_data"
occupancy_21 = pd.read_csv(local_path+r'/Daily_shelter_occupancy_current.csv')
occupancy_20 = pd.read_csv(local_path+r'/daily-shelter-occupancy-2020.csv')
occupancy_19 = pd.read_csv(local_path+r'/daily-shelter-occupancy-2019.csv')

# Merge multiple years' data, align date formats
date_col = "OCCUPANCY_DATE"
occupancy_19 = occupancy_19.drop("_id",axis=1)
occupancy_21 = occupancy_21.drop("_id",axis=1)
occupancy_19['OCCUPANCY_DATETIME'] = occupancy_19[date_col].apply(lambda dt: datetime.strptime(dt.replace("T"," "),"%Y-%m-%d %H:%M:%S"))
occupancy_21['OCCUPANCY_DATETIME'] = occupancy_21[date_col].apply(lambda dt: datetime.strptime(dt.replace("T"," "),"%Y-%m-%d %H:%M:%S"))
occupancy_19[date_col] = occupancy_19['OCCUPANCY_DATETIME'].apply(lambda dt: dt.strftime("%m/%d/%Y"))
occupancy_21[date_col] = occupancy_21['OCCUPANCY_DATETIME'].apply(lambda dt: dt.strftime("%m/%d/%Y"))
occupancy = pd.concat([occupancy_19,occupancy_20,occupancy_21],axis=0,ignore_index=True,sort=True)

# Create mappings for data transformation
post_col, city_col, address_col, province_col = 'SHELTER_POSTAL_CODE', 'SHELTER_CITY', 'SHELTER_ADDRESS', 'SHELTER_PROVINCE'
loc_cols = [post_col,'SHELTER_NAME','LATITUDE','LONGITUDE']
month_dict = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
shelter_dict = [{'label':x, 'value':x} for x in occupancy['SHELTER_NAME'].drop_duplicates()]
all_shelters = occupancy['SHELTER_NAME'].drop_duplicates().to_list()
all_sectors = occupancy['SECTOR'].drop_duplicates().to_list()
city_dict = [{'label':x, 'value':x} for x in occupancy['SHELTER_CITY'].drop_duplicates()]
sector_dict = [{'label':x, 'value':x} for x in occupancy['SECTOR'].drop_duplicates()]

# Remove dashes from postal data, impute spaces if missing
occupancy_ = occupancy.copy()
occupancy[post_col] = occupancy[post_col].apply(lambda x: x[:3] + " " + x[3:] if len(x)==6 else x)
occupancy[post_col] = occupancy[post_col].apply(lambda x: x.replace("-"," "))
# Remove typos, remove "floor" notations
occupancy_[address_col] = occupancy_[address_col].apply(lambda x: x.replace("Bathrust","Bathurst"))
occupancy_[address_col] = occupancy_[address_col].apply(lambda x: x.replace(", 2nd floor",""))

# Create full address using city and province
occupancy_["FULL_ADDRESS"] = occupancy_[address_col] + ", " + occupancy_[city_col] + ", " + occupancy_[province_col]

# Lat / long extraction using geopy
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="markkerenberg@gmail.com")

# Unique addresses for geocoder
unique_adds = occupancy_["FULL_ADDRESS"].drop_duplicates().to_frame()

# Geocode full addresses
#t0 = time.time()
unique_adds["LOCATION"] = unique_adds["FULL_ADDRESS"].apply(lambda x: geolocator.geocode(x))
#t1 = time.time()
#print(f"Time taken to geocode locations: {(t1-t0)/60}m")
unique_adds = unique_adds[unique_adds["LOCATION"].notnull()].reset_index(drop=True)
unique_adds["LATITUDE"] = unique_adds["LOCATION"].apply(lambda x: x.latitude)
unique_adds["LONGITUDE"] = unique_adds["LOCATION"].apply(lambda x: x.longitude)
unique_adds = unique_adds.drop("LOCATION",axis=1)

# Write coordinates to CSV
unique_adds.to_csv(data_path+r"/occupancy_coordinates.csv",sep=",",header=True,index=False)