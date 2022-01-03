# -*- coding: utf-8 -*-
# ======== Dash App ======== #

import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from datetime import datetime

# Heroku env variable definition
# ON_HEROKU = os.environ.get('ON_HEROKU')
# if ON_HEROKU:
#     # get the heroku port
#     port = int(os.environ.get('PORT', 8050))
# else:
#     port = 8050

# Get data files
#local_path = r'C:\Users\marke\Downloads\Datasets\Toronto_Homelessness'
#local_path = r'/Users/merenberg/Desktop/dash-project/underlying_data'
#local_path = r'/Users/markerenberg/Documents/Github/homelessness-dash/homelessness-dash/underlying_data'
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
local_path = ROOT_DIR + r'/underlying_data'
sna_export = pd.read_csv(local_path+r'/sna2018opendata_export.csv').fillna(0)
sna_rows = pd.read_csv(local_path+r'/sna2018opendata_keyrows.csv')
sna_cols = pd.read_csv(local_path+r'/sna2018opendata_keycolumns.csv')
#shelter_flow = pd.read_csv(local_path+r'/toronto-shelter-system-flow_may11.csv')
shelter_flow = pd.read_csv(local_path+r'/toronto-shelter-system-flow_may28.csv')
occupancy_21 = pd.read_csv(local_path+r'/Daily_shelter_occupancy_current.csv')
occupancy_20 = pd.read_csv(local_path+r'/daily-shelter-occupancy-2020.csv')
occupancy_19 = pd.read_csv(local_path+r'/daily-shelter-occupancy-2019.csv')


################### Shelter System Flow ###################
flow = shelter_flow.rename(columns={'date(mmm-yy)':'date'})
month_dict = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
pop_groups = ['Chronic','Refugees','Families','Youth','Single Adult','Non-refugees']
inflow = ['returned_from_housing','returned_to_shelter','newly_identified']
outflow = ['moved_to_housing','no_recent_shelter_use']
age_cols = [col for col in flow.columns if 'age' in col and col != 'population_group_percentage']
gender_cols = [col for col in flow.columns if 'gender' in col]

# Create month, year, datetime columns
flow['month_name'] = flow['date'].apply(lambda st: st[:3])
flow['month'] = flow['month_name'].replace(dict((y,x) for x,y in month_dict.items()),inplace=False)
flow['month_str']=['0'+str(x) if len(str(x))!=2 else str(x) for x in flow.month]  # add leading zeroes
flow['year'] = flow['date'].apply(lambda st: int(st[len(st)-2:]))
flow['year_full'] = flow['year'].apply(lambda yr: yr+2000)
flow['date_full'] = flow.apply(lambda row: '20'+str(row['year'])+row['month_str']+'01',axis=1)
flow['datetime'] = flow['date_full'].apply(lambda x: pd.to_datetime(str(x), format='%Y%m%d'))
date_cols = ['date','month','month_name','month_str','datetime','year','year_full']
month_dict_v1 = [{'label':x, 'value':x} for x in flow['month_name'].drop_duplicates()]
year_dict = [{'label':x, 'value':x} for x in flow['year_full'].drop_duplicates()]
popgroup_dict = [{'label':x, 'value':x} for x in flow['population_group'].drop_duplicates() if x != "All Population"]

# Line graph of Actively Experiencing Homelessness
actively = flow.loc[(flow['population_group'].isin(pop_groups+['All Population'])),\
                    date_cols+['actively_homeless','population_group']]
active_fig = px.line(actively,x="datetime",y="actively_homeless",color='population_group',\
                     title='Population Actively Experiencing Homelessness In Toronto Shelters')
active_fig.update_xaxes(title_text='Time',\
                        ticktext=actively['date'],
                        tickvals=actively['datetime'])
active_fig.update_yaxes(title_text='Population Count')
active_fig.update_layout(title_x=0.5,showlegend=True, \
                         autosize=True,
                         height=600,
                         width=1400)
active_fig.update_traces(mode='markers+lines')
active_fig.update_traces(patch={"line": {"color": "black", "width": 6, "dash": 'dot'}}, selector={"legendgroup": "All Population"})
#plotly.offline.plot(active_fig)

# Grouped bar plot to show inflow vs outflow
all_population = flow.loc[flow['population_group']=='All Population',:]
pop_melt = pd.melt(all_population,id_vars=date_cols+['population_group'],\
                   value_vars=inflow+outflow,var_name='housing_status',value_name='count')
pop_melt['flow_type'] = ['Inflow' if flow_type in inflow else 'Outflow' for flow_type in pop_melt['housing_status']]
flow_fig = px.bar(pop_melt,x="datetime",y="count",barmode="group",\
                  color="flow_type",title="Toronto Shelter System Inflow vs Outflow",
                  hover_name="housing_status",hover_data=["housing_status","flow_type","count"],\
                  labels={'flow_type': "Flow Type", "housing_status": "Housing Status",\
                              "population_group":"Population Group","datetime": "Time", "count": "Population Count"},\
                  color_discrete_map={'Inflow':'red','Outflow':'green'})
flow_fig.update_layout(title_x=0.5,showlegend=True, \
                         autosize=True,
                         height=600,
                         width=1400)
#plotly.offline.plot(flow_fig)

# Line plot of shelter flow by age
age_melt = pd.melt(all_population,id_vars=date_cols+['population_group'],\
                   value_vars=age_cols,var_name='age_group',value_name='count')
age_fig = px.line(age_melt,x="datetime",y="count",color='age_group',\
                     title='Active Shelter Population By Age Demographic',\
                     labels={'age_group': "Age Demographic","datetime":"Time","count":"Population Count"})
age_fig.update_xaxes(title_text='Time',\
                        ticktext=age_melt['date'],
                        tickvals=age_melt['datetime'])
age_fig.update_yaxes(title_text='Population Count')
age_fig.update_layout(title_x=0.5,showlegend=True, autosize=False,width=750,\
                      legend=dict(orientation="h",yanchor="bottom",xanchor="left",title='',\
                                  y=1.02,x=0.01),\
                      margin=dict(l=100))
age_fig.update_traces(mode='markers+lines')
#plotly.offline.plot(age_fig)

# Line plot of shelter flow by gender
gend_melt = pd.melt(all_population,id_vars=date_cols+['population_group'],\
                   value_vars=gender_cols,var_name='gender_group',value_name='count')
gend_melt.loc[gend_melt['gender_group']=="gender_transgender,non-binary_or_two_spirit","gender_group"]="gender_transgender"
gend_fig = px.line(gend_melt,x="datetime",y="count",color='gender_group',\
                     title='Active Shelter Population By Gender Demographic',\
                     labels={'gender_group': "Gender Demographic","datetime":"Time","count":"Population Count"})
gend_fig.update_xaxes(title_text='Time',\
                        ticktext=gend_melt['date'],
                        tickvals=gend_melt['datetime'])
gend_fig.update_yaxes(title_text='Population Count')
gend_fig.update_layout(title_x=0.5,showlegend=True, autosize=False, \
                       legend=dict(orientation="h", yanchor="bottom", xanchor="left", title='', \
                                   y=1.02, x=0.01),\
                       margin=dict(l=100))
gend_fig.update_traces(mode='markers+lines')
#plotly.offline.plot(gend_fig)


################### Street Needs Assessment ###################
sna_export = sna_export.merge(sna_rows.iloc[:,:3],on='SNA RESPONSE CATEGORY')

# Pivot on question-response
q_cols = ['SNA RESPONSE CATEGORY','QUESTION/CATEGORY DESCRIPTION','RESPONSE']
shelter_cols = ['OUTDOORS','CITY-ADMINISTERED SHELTERS','24-HR RESPITE','VAW SHELTERS']
dem_cols = ['SINGLE ADULTS','FAMILY','YOUTH']
total_cols = ['TOTAL']
response_types = {'Total':total_cols,'Location':shelter_cols,'Demographic':dem_cols}

sna_melt = sna_export.melt(id_vars=q_cols,value_vars=shelter_cols+dem_cols+['TOTAL'],
                           var_name='GROUP',value_name='COUNT')

# Track count/average responses
avg_cols = [cat for cat in sna_melt['SNA RESPONSE CATEGORY'].unique() if ('AVERAGE' in cat)]
cnt_cols = [cat for cat in sna_melt['SNA RESPONSE CATEGORY'].unique() if ('COUNT' in cat)]

# Q1: Total Survey Count
q1 = sna_melt.loc[sna_melt['SNA RESPONSE CATEGORY']=="TOTALSURVEYS",]
#q1_bar = px.bar(q1.loc[q1['GROUP'].isin(shelter_cols),].sort_values('COUNT',ascending=False),
#                x="GROUP",y="COUNT",text="COUNT",color="GROUP",
#                height=500,
#                labels=dict(GROUP="LOCATION"))
#q1_bar.update_layout(showlegend=False)
#plotly.offline.plot(q1_bar)

# Q4: How much time (on avg) homeless in last 12 months
q4 = sna_melt.loc[sna_melt['SNA RESPONSE CATEGORY']=="4_TIMEHOMELESSAVERAGE",]
#q4_line = px.line(q4.loc[q4['GROUP'].isin(shelter_cols),],
#                  x='GROUP',y='COUNT',text='COUNT')
#plotly.offline.plot(q4_line)

q1_dat = q1.loc[q1['GROUP'].isin(shelter_cols),].sort_values('COUNT',ascending=False)
q1_sort_order = dict(zip(q1_dat['GROUP'],list(range(1,5))))
q4_dat = q4.loc[q4['GROUP'].isin(shelter_cols),]
q4_dat = q4_dat.iloc[q4_dat['GROUP'].map(q1_sort_order).argsort()]
q1_bar = make_subplots(specs=[[{"secondary_y": True}]])
q1_bar.add_trace(go.Bar(x=q1_dat['GROUP'],y=q1_dat['COUNT'],text=q1_dat['COUNT'],
    textposition='outside',
    #marker_color=dict(zip(q1_dat['GROUP'], plotly.colors.qualitative.Plotly[:len(q1_dat['GROUP'])])),
    name='Homeless Count'),
    secondary_y=False
)
q1_bar.add_trace(go.Scatter(x=q4_dat['GROUP'],y=q4_dat['COUNT'],text=q4_dat['COUNT'],
                            name='Avg Homeless Duration'),
                 secondary_y=True)
q1_bar.update_yaxes(title_text="Count", secondary_y=False,title_font={"size": 12})
q1_bar.update_yaxes(title_text="Duration (Days)", secondary_y=True,title_font={"size": 12})
q1_bar.update_layout(autosize=False,height=550,width=750,margin=dict(l=100),
                     legend=dict(orientation='h',yanchor="bottom",xanchor="right",
                                 y=1.02,x=1)
                     )

# Q2: People staying with you
q2 = sna_melt.loc[sna_melt['QUESTION/CATEGORY DESCRIPTION']=="What family members are staying with you tonight?",]
q2_pie = px.pie(q2.loc[(q2['RESPONSE'].notnull())&(q2['GROUP']=="TOTAL"),],
                height=500,
                values="COUNT",names="RESPONSE")
#plotly.offline.plot(q2_pie)

# Q6: What happened that caused you to lose your housing most recently?
q6 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION']=="What happened that caused you to lose your housing most recently?")\
                   &(sna_melt['RESPONSE'].notnull()) \
                   &(sna_melt['RESPONSE']!="Other"),]
q6_bar = px.bar(q6.loc[q6['GROUP'].isin(shelter_cols),].sort_values(by="COUNT",ascending=False),\
                 x="RESPONSE", y="COUNT", color="GROUP", \
                 text='COUNT')
q6_bar.update_traces(marker_color='darkorange')
#plotly.offline.plot(q6_bar)

# Question 7: Have you stayed in an emergency shelter in the past 12 months?
q7 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION']=="Have you stayed in an emergency shelter in the past 12 months?")&\
                  (~sna_melt['RESPONSE'].isin(["Don’t know","Decline to answer"]))&\
                  (sna_melt['RESPONSE'].notnull()),]

q7_bar = px.bar(q7.loc[q7['GROUP'].isin(shelter_cols),],\
                 x="RESPONSE", y="COUNT", color="GROUP", \
                 title="Have you stayed in an emergency shelter in the past 12 months?",\
                 text='COUNT')
#plotly.offline.plot(q7_bar)

# Question 8: Did you stay overnight at any Winter Services this past winter?
q8 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION']=="Did you stay overnight at any of the following Winter Services this past winter?")\
                   &(~sna_melt['RESPONSE'].isin(["Don’t know","Decline to answer"]))\
                   &(sna_melt['RESPONSE'].notnull()),]

q8_bar = px.bar(q8.loc[q8['GROUP'].isin(shelter_cols),],\
                 x="RESPONSE", y="COUNT", color="GROUP", \
                 title="Did you stay overnight at any Winter Services this past winter?",\
                 text='COUNT')
#plotly.offline.plot(q8_bar)

# Q19: Health conditions
q19 = sna_melt.loc[(sna_melt['SNA RESPONSE CATEGORY'].str.contains("19_"))\
                   &(sna_melt['RESPONSE']=='Yes'),].drop("RESPONSE",axis=1)
q19['RESPONSE'] = q19['QUESTION/CATEGORY DESCRIPTION'].str[66:]
q19_bar = px.bar(q19.loc[q19['GROUP'].isin(shelter_cols),].sort_values(by='COUNT',ascending=False),\
                 x="RESPONSE", y="COUNT", color="GROUP",\
                 text='COUNT')
q19_bar.update_traces(marker_color='sienna')

# Question 22: What would help you personally find housing?
q22 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION']=="Please tell me which ones would help you personally find housing.")\
                   &(~sna_melt['RESPONSE'].isin(["Don't know","Decline to answer"]))\
                   &(sna_melt['RESPONSE'].notnull()),]

q22_bar = px.bar(q22.loc[q22['GROUP'].isin(shelter_cols),],\
                 x="RESPONSE", y="COUNT", color="GROUP", \
                 title="What would help you personally find housing?",\
                 text='COUNT')
q22_bar.update_traces(marker_color='crimson')
#plotly.offline.plot(q22_bar)

# Question 23: In the past 6 months, have you
q23 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION'].str.contains("In the past 6 months, have you"))\
                   &(sna_melt['RESPONSE']=='Yes'),].drop("RESPONSE",axis=1)
q23['RESPONSE'] = q23['QUESTION/CATEGORY DESCRIPTION'].str[32:]

q23_bar = px.bar(q23.loc[q23['GROUP'].isin(shelter_cols),].sort_values(by='COUNT',ascending=False),\
                 x="RESPONSE", y="COUNT", color="GROUP",\
                 text='COUNT')
q23_bar.update_yaxes(title_text="Count", title_font={"size": 12})
q23_bar.update_layout(autosize=False,height=550,width=700,margin=dict(l=100),showlegend=False)
q23_bar.update_traces(marker_color='forestgreen')
#plotly.offline.plot(q23_bar)


################### Daily Shelter Occupancy ###################

# Merge multiple years' data, align date formats
date_col = "OCCUPANCY_DATE"
occupancy_19 = occupancy_19.drop("_id",axis=1)
occupancy_21 = occupancy_21.drop("_id",axis=1)
occupancy_19['OCCUPANCY_DATETIME'] = occupancy_19[date_col].apply(lambda dt: datetime.strptime(dt.replace("T"," "),"%Y-%m-%d %H:%M:%S"))
occupancy_21['OCCUPANCY_DATETIME'] = occupancy_21[date_col].apply(lambda dt: datetime.strptime(dt.replace("T"," "),"%Y-%m-%d"))
occupancy_19[date_col] = occupancy_19['OCCUPANCY_DATETIME'].apply(lambda dt: dt.strftime("%m/%d/%Y"))
occupancy_21[date_col] = occupancy_21['OCCUPANCY_DATETIME'].apply(lambda dt: dt.strftime("%m/%d/%Y"))

# Make changes to match 2021 occupancy data with previous years
occ_21_cols = {"LOCATION_NAME": "SHELTER_NAME",
               "LOCATION_ADDRESS": "SHELTER_ADDRESS",
               "LOCATION_POSTAL_CODE": "SHELTER_POSTAL_CODE",
               "LOCATION_CITY": "SHELTER_CITY",
               "LOCATION_PROVINCE": "SHELTER_PROVINCE"}
occupancy_21 = occupancy_21.rename(columns=occ_21_cols)
occupancy_bed = occupancy_21[occupancy_21["CAPACITY_TYPE"]=="Bed Based Capacity"].reset_index(drop=True)
occupancy_room = occupancy_21[occupancy_21["CAPACITY_TYPE"]=="Room Based Capacity"].reset_index(drop=True)
occupancy_bed["OCCUPANCY"] = occupancy_bed["OCCUPIED_BEDS"].astype("int")
occupancy_bed["CAPACITY"] = occupancy_bed["CAPACITY_ACTUAL_BED"].astype("int")
occupancy_room["OCCUPANCY"] = occupancy_room["OCCUPIED_ROOMS"].astype("int")
occupancy_room["CAPACITY"] = occupancy_room["CAPACITY_ACTUAL_ROOM"].astype("int")
# Group by shelter, merge two types of shelter data
occupancy_cols = ["OCCUPANCY_DATE","ORGANIZATION_NAME","SHELTER_NAME","SHELTER_ADDRESS",
                  "SHELTER_CITY","SHELTER_PROVINCE","SHELTER_POSTAL_CODE","PROGRAM_NAME",
                  "SECTOR"]
occupancy_21 = pd.concat([occupancy_bed[occupancy_cols+["OCCUPANCY","CAPACITY"]],\
                         occupancy_room[occupancy_cols+["OCCUPANCY","CAPACITY"]]],\
                         axis=0,ignore_index=True,sort=False)

# Merge all years' occupancy data
occupancy = pd.concat([occupancy_19.drop(["FACILITY_NAME","OCCUPANCY_DATETIME"],axis=1),
                       occupancy_20.drop("FACILITY_NAME",axis=1),
                       occupancy_21],axis=0,ignore_index=True,sort=True)

# Drop null names/postal codes
occupancy = occupancy[(occupancy["SHELTER_NAME"].notnull())&\
                      (occupancy["SHELTER_POSTAL_CODE"].notnull())].reset_index(drop=True)

#ssl._create_default_https_context = ssl._create_unverified_context
#nomi = pgeocode.Nominatim('ca')
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

# Read in coordinates for each shelter's address
occupancy_coords = pd.read_csv(local_path+r"/occupancy_coordinates.csv")

# Merge back with occupancy data
occupancy_ = occupancy_.merge(occupancy_coords,how='inner',on='FULL_ADDRESS')

# Previous code for extracting lat/long from postal codes
#unique_postal = occupancy[post_col].drop_duplicates().to_frame()
#unique_postal['LATITUDE'] = unique_postal[post_col].apply(lambda x: nomi.query_postal_code(x)['latitude'])
#unique_postal['LONGITUDE'] = unique_postal[post_col].apply(lambda x: nomi.query_postal_code(x)['longitude'])
#occupancy_ = occupancy_.merge(unique_postal,how='inner',on='SHELTER_POSTAL_CODE')

# Create month,year columns
occupancy_['MONTH'] = occupancy_['OCCUPANCY_DATE'].apply(lambda x: int(x[:2]))
occupancy_['MONTH_STR']=['0'+str(x) if len(str(x))!=2 else str(x) for x in occupancy_.MONTH]  # add leading zeroes
occupancy_['MONTH_NAME'] = occupancy_['MONTH'].replace(month_dict,inplace=False)
occupancy_['YEAR'] = occupancy_['OCCUPANCY_DATE'].apply(lambda x: int(x[6:]))
occupancy_['MONTH_YEAR'] = occupancy_.apply(lambda row: row['MONTH_NAME']+"-"+str(row['YEAR']),axis=1)
occupancy_['MONTH_DATE'] = occupancy_.apply(lambda row: str(row['YEAR'])+row['MONTH_STR']+'01',axis=1)
occ_month_cols = ["MONTH","MONTH_STR","MONTH_NAME","YEAR","MONTH_YEAR","MONTH_DATE"]

# Group by date, take sum of occupancy/capacity
occ_sums = occupancy_.groupby(["OCCUPANCY_DATE"]+loc_cols,as_index=False)\
                     .agg({'OCCUPANCY':'sum','CAPACITY':'sum'})
occ_sums['CAPACITY_PERC'] = occ_sums['OCCUPANCY']/occ_sums['CAPACITY']*100
occ_sums['WEIGHTED_CAP'] = occ_sums['CAPACITY_PERC']*occ_sums['CAPACITY']

# Group by location (postal) and take avg across month of occupancy
map_dat = occ_sums.groupby(loc_cols,as_index=False)\
                    .agg({'OCCUPANCY':'mean','CAPACITY':'mean','CAPACITY_PERC':'mean','WEIGHTED_CAP':'mean'})

# Need to scale bubble size
scale = map_dat['CAPACITY'].max()

# SHELTER MAP PLOT
shelter_map = go.Figure()
mapbox_key = "pk.eyJ1IjoibWFya2VyZW5iZXJnIiwiYSI6ImNqd29oZ205azFybXk0OXA2MG93OXp1aGoifQ.fUo4sj9PExFysDzHwcr69Q"

shelter_map.add_trace(go.Scattermapbox(
        lat=map_dat['LATITUDE'],
        lon=map_dat['LONGITUDE'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=map_dat['CAPACITY']/scale*100,
            color=map_dat['CAPACITY_PERC'],
            colorscale=[[0, 'rgb(255,230,230)'], [1, 'rgb(255,0,0)']],
            cmin=50,
            cmax=100,
            opacity=0.7
        ),
        text="Shelter Name: " + map_dat['SHELTER_NAME'].astype(str)\
             + "<br><b>Avg Capacity (%): " + map_dat['CAPACITY_PERC'].astype(str)\
            + "</b><br>Avg Occupancy: " + map_dat['OCCUPANCY'].astype(str),
        hoverinfo='text',
        hoverlabel= dict(bgcolor='white',\
                         font=dict(color='black'))
    )
)

shelter_map.update_layout(
    title="Shelter Capacity in Greater Toronto Area (2019-2021)",
    autosize=True,
    height=600,
    width=1400,
    hovermode='closest',
    showlegend=False,
    mapbox=dict(
        accesstoken=mapbox_key,
        bearing=0,
        center=dict(
            lat=43.686820,
            lon=-79.393590
        ),
        pitch=0,
        zoom=10,
        style='light'
    ),
)
#plotly.offline.plot(shelter_map)

# SHELTER TREND PLOTS
sec_trend = occupancy_.groupby(occ_month_cols+['SECTOR'],as_index=False)\
                     .agg({'OCCUPANCY':'sum','CAPACITY':'sum'})
sec_trend['CAPACITY_PERC'] = sec_trend['OCCUPANCY']/sec_trend['CAPACITY']*100
sec_trend['WEIGHTED_CAP'] = sec_trend['CAPACITY_PERC']*sec_trend['CAPACITY']
sec_trend = sec_trend.sort_values(by='MONTH_DATE')
sh_trend = occupancy_.groupby(occ_month_cols+loc_cols,as_index=False)\
                     .agg({'OCCUPANCY':'sum','CAPACITY':'sum'})
sh_trend['CAPACITY_PERC'] = sh_trend['OCCUPANCY']/sh_trend['CAPACITY']*100
sh_trend['WEIGHTED_CAP'] = sh_trend['CAPACITY_PERC']*sh_trend['CAPACITY']
sh_trend = sh_trend.sort_values(by='MONTH_DATE')

sec_trend_fig = px.line(sec_trend,x="MONTH_DATE",y='CAPACITY_PERC',color='SECTOR',
                        line_shape='spline',
                        range_y=[np.min(sec_trend['CAPACITY_PERC'])-5,np.max(sec_trend['CAPACITY_PERC'])+5],
                        title='Shelter Capacity By Sector',
                        render_mode="svg")
sec_trend_fig.update_xaxes(title_text='Time',
                           ticktext=sec_trend['MONTH_YEAR'],
                           tickvals=sec_trend['MONTH_DATE'])
sec_trend_fig.update_yaxes(title_text='Shelter Capacity (%)')
sec_trend_fig.update_layout(title_x=0.5,showlegend=False,
                            legend=dict(
                            yanchor="top",y=0.99,
                            xanchor="left",x=0.01))
#plotly.offline.plot(sec_trend_fig)

sh_trend_fig = px.line(sh_trend,x='MONTH_DATE',y='CAPACITY_PERC',color='SHELTER_NAME',
                    line_shape='spline',
                    range_y=[np.min(sh_trend['CAPACITY_PERC'])-5,np.max(sh_trend['CAPACITY_PERC'])+5],
                    title='Shelter Capacity By Shelter',
                    render_mode="svg")
sh_trend_fig.update_xaxes(title_text='Time',
                          ticktext=sh_trend['MONTH_YEAR'],
                          tickvals=sh_trend['MONTH_DATE'])
sec_trend_fig.update_yaxes(title_text='Shelter Capacity (%)')
sh_trend_fig.update_layout(title_x=0.5,showlegend=False)
#plotly.offline.plot(sh_trend_fig)


# Helper function to find shelter name using lat/lon
def find_shelter(point):
    '''
    takes in JSON dump from map selectedData and returns shelter name
    :param point: dictionary of plotly map point, including lat/lon coordinates
    :return: string shelter_name
    '''
    text = point['text']
    return text[(text.find("Shelter Name: ")+len("Shelter Name: ")):text.find("<br>")]

##############################################################
                    #     APP LAYOUT      #
##############################################################
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

colors = {
    'background': '#ffffff',
    'text': '#404040'
}

#sna_bar.update_layout(
#    plot_bgcolor=colors['background'],
#    paper_bgcolor=colors['background'],
#    font_color=colors['text']
#)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
#app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

server = app.server

app.layout = html.Div(children=[
    html.H1(children='Homelessness Dash',
            style={'textAlign': 'center','color': colors['text']}
            ),
    html.Br(),
    html.H5(children='Toronto Shelter System Flow Data',
            style={'textAlign': 'left',
                   'color': colors['text'],
                   'font-weight': 'bold',
                   'text-indent': '20px'}
            ),
    html.H6(
        "Public data on the people experiencing homelessness who are entering/leaving the shelter system",
        style={'textAlign': 'left', 'text-indent': '20px'}),
    html.Div([
        html.Div(["Filter By Year:",
              dcc.Checklist(id="flow_year",options=year_dict,value=[yr for yr in flow['year_full'].drop_duplicates()])],
        style={'textAlign':'left','float':'left','text-indent':'40px','display': 'inline-block','width':'49%'}),
        html.Div(["Filter By Month:",
              dcc.RangeSlider(id="flow_month",min=1,max=12,step=1,value=[1,12],marks=month_dict)],\
        style={'textAlign':'left','float':'left','display': 'inline-block','width':'49%'})],
        style={'backgroundColor': 'rgb(250, 250, 250)'},
        className="row"),
    html.Div([html.Div(["Filter By Population Group:",\
              dcc.Checklist(id="flow_group",options=popgroup_dict,\
                           value=[sh for sh in flow['population_group'].drop_duplicates() if sh != 'All Population'])],
                    style={'textAlign':'left','text-indent':'40px','display':'inline-block','width':'80%'}),
              html.H6("",style={'textAlign':'left','display':'inline-block','width':'20%'})],
        style={'borderBottom': 'thin lightgrey solid', 'backgroundColor': 'rgb(250, 250, 250)'},
        className="row"),
    html.Br(),
    html.Div([dcc.Graph(id="active_line", figure=active_fig)],
             style={'textAlign': 'center'}),
    html.Div([dcc.Graph(id="flowtype_chart", figure=flow_fig)],
             style={'textAlign': 'center'}),
    html.Br(),
    html.Div([
        html.Div([dcc.Graph(id="age_line",figure=age_fig)],
                  style={'textAlign':'center','width':'52%','height':'600','display': 'inline-block'}),
        html.Div([dcc.Graph(id="gender_line",figure=gend_fig)],
                  style={'textAlign':'center','width':'48%','height':'600', 'display': 'inline-block'})
    ],className="row"),
    html.Br(),
    html.H5(children='Toronto Shelter Occupancy Data',
            style={'textAlign': 'left',
                   'color': colors['text'],
                   'font-weight': 'bold',
                   'text-indent': '20px'}
            ),
    html.H6(
        "Public data on the monthly occupancy and capacity of Toronto’s shelter system",
        style={'textAlign': 'left', 'text-indent': '20px'}),
    html.Br(),
    html.Div([
        html.Div(["Filter By Year:",
              dcc.Checklist(id="shelter_year",options=[{'label':x, 'value':x} for x in occupancy_['YEAR'].drop_duplicates()],\
                            value=[yr for yr in occupancy_['YEAR'].drop_duplicates()])],
        style={'textAlign':'left','float':'left','text-indent':'40px','display': 'inline-block','width':'49%'}),
        html.Div(["Filter By Month:",
              dcc.RangeSlider(id="shelter_month",min=1,max=12,step=1,value=[1,12],marks=month_dict)],\
        style={'textAlign':'left','float':'left','display': 'inline-block','width':'49%'})],
        style={'backgroundColor': 'rgb(250, 250, 250)'},
        className="row"),
    html.Div([html.Div(["Filter By Sector:",
                 dcc.Checklist(id="sector",options=sector_dict,value=[sh for sh in occupancy['SECTOR'].drop_duplicates()])],
                 style={'textAlign':'left','float':'right','text-indent':'40px','display': 'inline-block','width':'49%'}),
              html.H6("",style={'textAlign':'left','display':'inline-block','width':'49%'})],
        style={'borderBottom': 'thin lightgrey solid', 'backgroundColor': 'rgb(250, 250, 250)'},
        className="row"),
    html.Div([dcc.Graph(id="shelter_map",figure=shelter_map)],
             style={'textAlign':'center'}),
    # Test Pre just to see selection output
    #html.Div([
    #    dcc.Markdown("Selection Data"),
    #    html.Pre(id='selected-data'),
    #    html.Pre(id='selected-data-2'),
    #    html.Pre(id='selected-data-3')
    #]),
    html.Div([
        html.Div([dcc.Graph(id="sector_trend",figure=sec_trend_fig)],
                  style={'textAlign':'center','width':'50%','height':'400','text-indent':'20px','display': 'inline-block'}),
        html.Div([dcc.Graph(id="shelter_trend",figure=sh_trend_fig)],
                  style={'textAlign':'center','width':'50%','height':'400','text-indent':'10px', 'display': 'inline-block'})
    ],className="row"),
    html.Br(),
    html.H5(children='Street Needs Assessment: 2018 Results',
            style={'textAlign': 'left',
                   'color': colors['text'],
                   'font-weight': 'bold',
                   'text-indent':'20px'}
            ),
    html.H6("The Streets Needs Assessment is a City-wide point-in-time count and survey of people experiencing homelessness in Toronto.",
            style={'textAlign':'left','text-indent':'20px'}),
    html.Br(),
    html.Div([
        html.Div(["On an arbitrary night in 2018, how many people were homeless in Toronto?",
                  dcc.Graph(id="q1_bar",figure=q1_bar)],
                  style={'textAlign':'center','width':'48%', 'display': 'inline-block'}),
        html.Div(["Of those experiencing homelessness, what family members are staying with them??",
                  dcc.Graph(id="q2_pie",figure=q2_pie)],
                  style={'textAlign':'center','width':'48%', 'display': 'inline-block'})
    ],className="row"),
    html.Br(),
    html.Div([
        html.Div(["In the past 6 months, have you:",
                  dcc.Graph(id="q23_bar",figure=q23_bar)],
                  style={'textAlign':'center','width':'48%', 'display': 'inline-block'}),
        html.Div(["Do you identify as having any of the following health conditions:",
                  dcc.Graph(id="q19_bar",figure=q19_bar)],
                  style={'textAlign':'center','width':'48%', 'display': 'inline-block'})
    ],className="row"),
    html.Br(),
    html.Div(["What happened that caused you to lose your housing most recently?",
              dcc.Graph(id="q6_bar",figure=q6_bar)
              ],
             style={'textAlign':'center'}
    ),
    html.Br(),
    html.Div(["What would help you personally find housing?",
              dcc.Graph(id="q22_bar",figure=q22_bar)
              ],
             style={'textAlign':'center'}
    )
])

@app.callback(
    Output("active_line","figure"),
    Output("flowtype_chart","figure"),
    Output("age_line", "figure"),
    Output("gender_line", "figure"),
    Input("flow_year","value"),
    Input("flow_month","value"),
    Input("flow_group","value"),
)
def update_flow_graphs(flow_year,flow_month,flow_group):
    years_to_use = [2020,2021] if flow_year == None else flow_year
    months_to_use = list(month_dict.keys()) if flow_month == None else list(month_dict.keys())[(flow_month[0] - 1):flow_month[-1]]
    selected_groups = ["All Population"] if flow_group == None else flow_group
    active_chart_groups = pop_groups+["All Population"] if flow_group == None else flow_group+["All Population"]

    # Line graph of Actively Experiencing Homelessness
    actively = flow.loc[(flow['population_group'].isin(active_chart_groups))& \
                        (flow['month'].isin(months_to_use))& \
                        (flow['year_full'].isin(years_to_use)), \
                        date_cols + ['actively_homeless', 'population_group']]
    active_fig = px.line(actively, x="datetime", y="actively_homeless", color='population_group', \
                         title='Population Actively Experiencing Homelessness In Toronto Shelters')
    active_fig.update_xaxes(title_text='Time', \
                            ticktext=actively['date'],
                            tickvals=actively['datetime'])
    active_fig.update_yaxes(title_text='Population Count')
    active_fig.update_layout(title_x=0.5, showlegend=True, \
                             autosize=True,
                             height=600,
                             width=1400)
    active_fig.update_traces(mode='markers+lines',
                             patch={"line": {"color": "black", "width": 6, "dash": 'dot'}},
                             selector={"legendgroup": "All Population"})

    # Grouped bar plot to show inflow vs outflow
    all_population = flow.loc[(flow['population_group'].isin(selected_groups))&\
                              (flow['month'].isin(months_to_use))&\
                              (flow['year_full'].isin(years_to_use)), :]
    pop_melt = pd.melt(all_population, id_vars=date_cols + ['population_group'], \
                       value_vars=inflow + outflow, var_name='housing_status', value_name='count')
    pop_melt['flow_type'] = ['Inflow' if flow_type in inflow else 'Outflow' for flow_type in pop_melt['housing_status']]
    flow_fig = px.bar(pop_melt, x="datetime", y="count", barmode="group", \
                      color="flow_type", title="Toronto Shelter System Inflow vs Outflow",
                      hover_name="housing_status", hover_data=["housing_status","population_group","flow_type","count"], \
                      labels={'flow_type': "Flow Type", "housing_status": "Housing Status",\
                              "population_group":"Population Group","datetime": "Time", "count": "Population Count"}, \
                      color_discrete_map={'Inflow': 'red', 'Outflow': 'green'})
    flow_fig.update_layout(title_x=0.5, showlegend=True, \
                           autosize=True,
                           height=600,
                           width=1400)
    # Line plot of shelter flow by age
    age_grouped = all_population.groupby(date_cols,as_index=False)\
                                .agg({col:"sum" for col in age_cols})\
                                .sort_values(by="datetime")
    age_melt = pd.melt(age_grouped, id_vars=date_cols, \
                       value_vars=age_cols, var_name='age_group', value_name='count')
    age_fig = px.line(age_melt, x="datetime", y="count", color='age_group', \
                      title='Active Shelter Population By Age Demographic', \
                      labels={'age_group': "Age Demographic", "datetime": "Time", "count": "Population Count"})
    age_fig.update_xaxes(title_text='Time', \
                         ticktext=age_melt['date'],
                         tickvals=age_melt['datetime'])
    age_fig.update_yaxes(title_text='Population Count')
    age_fig.update_layout(title_x=0.5, showlegend=True, autosize=False, width=750, \
                          legend=dict(orientation="h", yanchor="bottom", xanchor="left", title='', \
                                      y=1.02, x=0.01), \
                          margin=dict(l=100))
    age_fig.update_traces(mode='markers+lines')
    # Line plot of shelter flow by gender
    gend_grouped = all_population.groupby(date_cols, as_index=False) \
                                .agg({col: "sum" for col in gender_cols}) \
                                .sort_values(by="datetime")
    gend_melt = pd.melt(gend_grouped, id_vars=date_cols, \
                        value_vars=gender_cols, var_name='gender_group', value_name='count')
    gend_melt.loc[gend_melt[
                      'gender_group'] == "gender_transgender,non-binary_or_two_spirit", "gender_group"] = "gender_transgender"
    gend_fig = px.line(gend_melt, x="datetime", y="count", color='gender_group', \
                       title='Active Shelter Population By Gender Demographic', \
                       labels={'gender_group': "Gender Demographic", "datetime": "Time", "count": "Population Count"})
    gend_fig.update_xaxes(title_text='Time', \
                          ticktext=gend_melt['date'],
                          tickvals=gend_melt['datetime'])
    gend_fig.update_yaxes(title_text='Population Count')
    gend_fig.update_layout(title_x=0.5, showlegend=True, autosize=False, \
                           legend=dict(orientation="h", yanchor="bottom", xanchor="left", title='', \
                                       y=1.02, x=0.01), \
                           margin=dict(l=100))
    gend_fig.update_traces(mode='markers+lines')
    return active_fig, flow_fig, age_fig, gend_fig

@app.callback(
    Output("q2_pie","figure"),
    Output("q23_bar","figure"),
    Output("q19_bar","figure"),
    Output("q6_bar","figure"),
    Output("q22_bar","figure"),
    Input("q1_bar","clickData"),
    Input("q1_bar","selectedData"),
)
def update_street_needs(clickData,selectedData):
    # STREET NEEDS
    click_type = ["TOTAL"] if clickData==None else [clickData["points"][0]["x"]]
    select_type = None if selectedData == None else [point["x"] for point in selectedData["points"]]
    group_type = click_type if select_type == None else select_type
    q2_pie = px.pie(q2.loc[(q2['RESPONSE'].notnull())&\
                           (q2['GROUP'].isin(group_type)),],
                    values="COUNT", names="RESPONSE")
    q23_bar = px.bar(q23.loc[q23['GROUP'].isin(group_type),].sort_values(by='COUNT', ascending=False), \
                     x="RESPONSE", y="COUNT", color="GROUP", \
                     text='COUNT')
    q19_bar = px.bar(q19.loc[q19['GROUP'].isin(group_type),].sort_values(by='COUNT', ascending=False), \
                     x="RESPONSE", y="COUNT", color="GROUP", \
                     text='COUNT')
    q6_bar = px.bar(q6.loc[q6['GROUP'].isin(group_type),].sort_values(by="COUNT", ascending=False), \
                    x="RESPONSE", y="COUNT", color="GROUP", \
                    text='COUNT')
    q22_bar = px.bar(q22.loc[q22['GROUP'].isin(group_type),].sort_values(by="COUNT", ascending=False), \
                    x="RESPONSE", y="COUNT", color="GROUP", \
                    text='COUNT')
    q23_bar.update_layout(margin=dict(l=100))
    q23_bar.update_yaxes(title_text="Count", title_font={"size": 12})
    q23_bar.update_xaxes(title_text="")
    q23_bar.update_layout(autosize=False, height=550, width=800, margin=dict(l=100), showlegend=False)
    q23_bar.update_traces(marker_color='forestgreen')
    q19_bar.update_yaxes(title_text="Count", title_font={"size": 12})
    q19_bar.update_xaxes(title_text="")
    q19_bar.update_layout(autosize=False, height=550, width=725, margin=dict(l=100), showlegend=False)
    q19_bar.update_traces(marker_color='sienna')
    q6_bar.update_yaxes(title_text="Count", title_font={"size": 12})
    q6_bar.update_xaxes(title_text="")
    q6_bar.update_layout(autosize=False, height=550, margin=dict(l=100), showlegend=False)
    q6_bar.update_traces(marker_color='darkorange')
    q22_bar.update_yaxes(title_text="Count", title_font={"size": 12})
    q22_bar.update_xaxes(title_text="")
    q22_bar.update_layout(autosize=False, height=650, margin=dict(l=100), showlegend=False)
    q22_bar.update_traces(marker_color='crimson')
    return q2_pie, q23_bar, q19_bar, q6_bar, q22_bar

@app.callback(
    Output("shelter_map", "figure"),
    Input("shelter_year", "value"),
    Input("shelter_month", "value"),
    Input("sector", "value")
)
def update_shelter_map(shelter_year,shelter_month,sector):
    # Shelter Occupancy Map
    years_to_use = [2019, 2020, 2021] if shelter_year == None else shelter_year
    months_to_use = list(month_dict.keys()) if shelter_month == None else list(month_dict.keys())[(shelter_month[0] - 1):shelter_month[-1]]
    occ_sums = occupancy_[(occupancy_['YEAR'].isin(years_to_use))&\
                          (occupancy_['MONTH'].isin(months_to_use)) & \
                          (occupancy_['SECTOR'].isin(sector))] \
        .groupby(["OCCUPANCY_DATE"] + loc_cols, as_index=False) \
        .agg({'OCCUPANCY': 'sum', 'CAPACITY': 'sum'})
    occ_sums['CAPACITY_PERC'] = occ_sums['OCCUPANCY'] / occ_sums['CAPACITY'] * 100
    occ_sums['WEIGHTED_CAP'] = occ_sums['CAPACITY_PERC'] * occ_sums['CAPACITY']
    map_dat = occ_sums.groupby(loc_cols, as_index=False) \
        .agg({'OCCUPANCY': 'mean', 'CAPACITY': 'mean', 'CAPACITY_PERC': 'mean', 'WEIGHTED_CAP': 'mean'})
    scale = map_dat['CAPACITY'].max()
    shelter_map = go.Figure()
    shelter_map.add_trace(go.Scattermapbox(
        lat=map_dat['LATITUDE'],
        lon=map_dat['LONGITUDE'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=map_dat['CAPACITY'] / scale * 50,
            color=map_dat['CAPACITY_PERC'],
            colorscale=[[0, 'rgb(255,230,230)'], [1, 'rgb(255,0,0)']],
            cmin=50,
            cmax=100,
            opacity=0.7
        ),
        text="Shelter Name: " + map_dat['SHELTER_NAME'].astype(str) \
             + "<br><b>Avg Capacity (%): " + map_dat['CAPACITY_PERC'].astype(str) \
             + "</b><br>Avg Occupancy: " + map_dat['OCCUPANCY'].astype(str),
        hoverinfo='text',
        hoverlabel=dict(bgcolor='white', font=dict(color='black'))
    ))
    shelter_map.update_layout(
        title="Shelter Capacity in Greater Toronto Area",
        autosize=True,
        height=600,
        width=1400,
        hovermode='closest',
        showlegend=False,
        mapbox=dict(
            accesstoken=mapbox_key,
            bearing=0,
            center=dict(lat=43.686820, lon=-79.393590),
            pitch=0,
            zoom=10,
            style='light'
        ),
    )

    return shelter_map

@app.callback(
    Output("sector_trend", "figure"),
    Output("shelter_trend", "figure"),
    Input("shelter_map", "clickData"),
    Input("shelter_map", "selectedData"),
    Input("shelter_year", "value"),
    Input("shelter_month", "value"),
    Input("sector", "value")
)
def update_shelter_trend(shelterClick,shelterSelect,shelter_year,shelter_month,sector):
    years_to_use = [2019, 2020, 2021] if shelter_year == None else shelter_year
    months_to_use = list(month_dict.keys()) if shelter_month == None else list(month_dict.keys())[(shelter_month[0] - 1):shelter_month[-1]]
    shelter_click = all_shelters if shelterClick == None else [find_shelter(point) for point in shelterClick["points"]]
    shelter_select = all_shelters if shelterSelect == None else [find_shelter(point) for point in shelterSelect["points"]]
    shelter_names = shelter_click if shelterSelect == None else shelter_select
    last_copy = shelter_names.copy() if ((shelterClick != None) or (shelterSelect!=None)) else all_shelters
    last_selection = last_copy if ((shelterClick == None) or (shelterSelect==None)) else shelter_names
    selected_sector = occupancy_[occupancy_['SHELTER_NAME'].isin(last_selection)]['SECTOR'].drop_duplicates().to_list()
    sector = list(set(sector+selected_sector)) if ((shelterClick != None) or (shelterSelect != None)) else all_sectors if len(sector)==0 else sector
    # Trend Charts
    sec_trend = occupancy_[occupancy_['YEAR'].isin(years_to_use) & \
                           occupancy_['MONTH'].isin(months_to_use) & \
                           occupancy_['SHELTER_NAME'].isin(last_selection) & \
                           occupancy_['SECTOR'].isin(sector)] \
        .groupby(occ_month_cols+["SECTOR"], as_index=False) \
        .agg({'OCCUPANCY': 'sum', 'CAPACITY': 'sum'})
    sec_trend['CAPACITY_PERC'] = sec_trend['OCCUPANCY'] / sec_trend['CAPACITY'] * 100
    sec_trend['WEIGHTED_CAP'] = sec_trend['CAPACITY_PERC'] * sec_trend['CAPACITY']
    sec_trend = sec_trend.sort_values(by='MONTH_DATE')
    sh_trend = occupancy_[occupancy_['YEAR'].isin(years_to_use) & \
                          occupancy_['MONTH'].isin(months_to_use) & \
                          occupancy_['SHELTER_NAME'].isin(last_selection) & \
                          occupancy_['SECTOR'].isin(sector)] \
        .groupby(occ_month_cols + loc_cols, as_index=False) \
        .agg({'OCCUPANCY': 'sum', 'CAPACITY': 'sum'})
    sh_trend['CAPACITY_PERC'] = sh_trend['OCCUPANCY'] / sh_trend['CAPACITY'] * 100
    sh_trend['WEIGHTED_CAP'] = sh_trend['CAPACITY_PERC'] * sh_trend['CAPACITY']
    sh_trend = sh_trend.sort_values(by='MONTH_DATE')
    sector_trend = px.line(sec_trend, x="MONTH_DATE", y='CAPACITY_PERC', color='SECTOR',
                           line_shape='spline',
                           range_y=[np.min(sec_trend['CAPACITY_PERC']) - 5, np.max(sec_trend['CAPACITY_PERC']) + 5],
                           title='Shelter Capacity By Sector',
                           render_mode="svg")
    sector_trend.update_xaxes(title_text='Time',
                              ticktext=sec_trend["MONTH_YEAR"],
                              tickvals=sec_trend["MONTH_DATE"])
    sector_trend.update_yaxes(title_text='Shelter Capacity (%)')
    sector_trend.update_layout(title_x=0.5,showlegend=False)
    shelter_trend = px.line(sh_trend, x="MONTH_DATE", y='CAPACITY_PERC', color='SHELTER_NAME',
                            line_shape='spline',
                            range_y=[np.min(sh_trend['CAPACITY_PERC']) - 5, np.max(sh_trend['CAPACITY_PERC']) + 5],
                            title='Shelter Capacity By Shelter',
                            render_mode="svg")
    shelter_trend.update_xaxes(title_text='Time',
                               ticktext=sh_trend["MONTH_YEAR"],
                               tickvals=sh_trend["MONTH_DATE"])
    shelter_trend.update_yaxes(title_text='Shelter Capacity (%)')
    shelter_trend.update_layout(title_x=0.5,showlegend=False)
    return sector_trend,shelter_trend


if __name__ == '__main__':
    app.run_server(debug=True)