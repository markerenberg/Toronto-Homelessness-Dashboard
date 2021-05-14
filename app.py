# ======== Dash App ======== #

#import imports

import os
import time
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pgeocode
import ssl
import json


# Get data files
#local_path = r'C:\Users\marke\Downloads\Datasets\Toronto_Homelessness'
local_path = r'/Users/merenberg/Desktop/dash-project/underlying_data'
sna_export = pd.read_csv(local_path+r'/sna2018opendata_export.csv').fillna(0)
sna_rows = pd.read_csv(local_path+r'/sna2018opendata_keyrows.csv')
sna_cols = pd.read_csv(local_path+r'/sna2018opendata_keycolumns.csv')
shelter_flow = pd.read_csv(local_path+r'/toronto-shelter-system-flow_april27.csv')
#occupancy_curr = pd.read_csv(local_path+r'\Daily_shelter_occupancy_current.csv')
occupancy = pd.read_csv(local_path+r'/daily-shelter-occupancy-2020.csv')

################### Shelter System Flow ###################
inflow = ['newly_identified','returned_from_housing','returned_to_shelter']
outflow = ['moved_to_housing','no_recent_shelter_use']


################### Daily Shelter Occupancy ###################
ssl._create_default_https_context = ssl._create_unverified_context
nomi = pgeocode.Nominatim('ca')
post_col = 'SHELTER_POSTAL_CODE'
loc_cols = [post_col,'SHELTER_NAME','LATITUDE','LONGITUDE']
month_dict = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
shelter_dict = [{'label':x, 'value':x} for x in occupancy['SHELTER_NAME'].drop_duplicates()]
all_shelters = occupancy['SHELTER_NAME'].drop_duplicates().to_list()
all_sectors = occupancy['SECTOR'].drop_duplicates().to_list()
city_dict = [{'label':x, 'value':x} for x in occupancy['SHELTER_CITY'].drop_duplicates()]
sector_dict = [{'label':x, 'value':x} for x in occupancy['SECTOR'].drop_duplicates()]

# Remove dashes from postal data, impute spaces if missing
occupancy_ = occupancy.copy()
occupancy[post_col] = occupancy[post_col].apply(lambda x: x.replace("-"," "))
occupancy[post_col] = occupancy[post_col].apply(lambda x: x[:3] + " " + x[3:] if len(x)==6 else x)

# Extract lat/long from postal codes
unique_postal = occupancy[post_col].drop_duplicates().to_frame()
unique_postal['LATITUDE'] = unique_postal[post_col].apply(lambda x: nomi.query_postal_code(x)['latitude'])
unique_postal['LONGITUDE'] = unique_postal[post_col].apply(lambda x: nomi.query_postal_code(x)['longitude'])
occupancy_ = occupancy_.merge(unique_postal,how='inner',on='SHELTER_POSTAL_CODE')

# Create month,year columns
occupancy_['MONTH'] = occupancy_['OCCUPANCY_DATE'].apply(lambda x: int(x[:2]))
occupancy_['MONTH_NAME'] = occupancy_['MONTH'].replace(month_dict,inplace=False)
occupancy_['YEAR'] = occupancy_['OCCUPANCY_DATE'].apply(lambda x: int(x[6:]))
#occupancy_ = occupancy_.sort_values(by='MONTH')

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
    title="Shelter Capacity in Greater Toronto Area (2020)",
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
sec_trend = occupancy_.groupby(["MONTH","MONTH_NAME","SECTOR"],as_index=False)\
                     .agg({'OCCUPANCY':'sum','CAPACITY':'sum'})
sec_trend['CAPACITY_PERC'] = sec_trend['OCCUPANCY']/sec_trend['CAPACITY']*100
sec_trend['WEIGHTED_CAP'] = sec_trend['CAPACITY_PERC']*sec_trend['CAPACITY']
sec_trend = sec_trend.sort_values(by='MONTH')
sh_trend = occupancy_.groupby(["MONTH","MONTH_NAME"]+loc_cols,as_index=False)\
                     .agg({'OCCUPANCY':'sum','CAPACITY':'sum'})
sh_trend['CAPACITY_PERC'] = sh_trend['OCCUPANCY']/sh_trend['CAPACITY']*100
sh_trend['WEIGHTED_CAP'] = sh_trend['CAPACITY_PERC']*sh_trend['CAPACITY']
sh_trend = sh_trend.sort_values(by='MONTH')

sec_trend_fig = px.line(sec_trend,x='MONTH',y='CAPACITY_PERC',color='SECTOR',
                        line_shape='spline',
                        range_y=[np.min(sec_trend['CAPACITY_PERC'])-5,np.max(sec_trend['CAPACITY_PERC'])+5],
                        title='Shelter Capacity By Sector (2020)')
sec_trend_fig.update_xaxes(title_text='Month',
                           ticktext=sec_trend['MONTH_NAME'],
                           tickvals=sec_trend['MONTH'])
sec_trend_fig.update_yaxes(title_text='Shelter Capacity (%)')
sec_trend_fig.update_layout(title_x=0.5,showlegend=False,
                            legend=dict(
                            yanchor="top",y=0.99,
                            xanchor="left",x=0.01))
#plotly.offline.plot(sec_trend_fig)

sh_trend_fig = px.line(sh_trend,x='MONTH',y='CAPACITY_PERC',color='SHELTER_NAME',
                    line_shape='spline',
                    range_y=[np.min(sh_trend['CAPACITY_PERC'])-5,np.max(sh_trend['CAPACITY_PERC'])+5],
                    title='Shelter Capacity By Shelter (2020)')
sh_trend_fig.update_xaxes(title_text='Month',
                          ticktext=sh_trend['MONTH_NAME'],
                          tickvals=sh_trend['MONTH'])
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
#plotly.offline.plot(q6_bar)

# Question 7: Have you stayed in an emergency shelter in the past 12 months?
q7 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION']=="Have you stayed in an emergency shelter in the past 12 months?")\
                   &(~sna_melt['RESPONSE'].isin(["Don’t know","Decline to answer"]))\
                   &(sna_melt['RESPONSE'].notnull()),]

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

# Question 22: What would help you personally find housing?
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

q23_bar = px.bar(q23.loc[q23['GROUP'].isin(shelter_cols),].sort_values(by='COUNT',ascending=False),\
                 x="RESPONSE", y="COUNT", color="GROUP",\
                 text='COUNT')
q23_bar.update_yaxes(title_text="Count", title_font={"size": 12})
q23_bar.update_layout(autosize=False,height=550,width=700,margin=dict(l=100),showlegend=False)
#plotly.offline.plot(q23_bar)


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

app.layout = html.Div(children=[
    html.H1(children='Homelessness Dash',
            style={'textAlign': 'center','color': colors['text']}
            ),
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
        html.Div(["Filter By Time:",
              dcc.RangeSlider(id="shelter_year",min=1,max=12,step=1,value=[1,12],
                              marks=month_dict)],
        style={'textAlign':'left','float':'left','text-indent':'40px','display': 'inline-block','width':'49%'}),
        html.Div(["Filter By Sector:",
                 dcc.Checklist(id="sector",
                           options=sector_dict,
                           value=[sh for sh in occupancy['SECTOR'].drop_duplicates()])],
        style={'textAlign':'left','float':'right','text-indent':'40px','display': 'inline-block','width':'49%'})],
        style={'borderBottom': 'thin lightgrey solid',
        'backgroundColor': 'rgb(250, 250, 250)'},
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
                  style={'textAlign':'center','width':'48%','height':'400','text-indent':'10px','display': 'inline-block'}),
        html.Div([dcc.Graph(id="shelter_trend",figure=sh_trend_fig)],
                  style={'textAlign':'center','width':'48%','height':'400','text-indent':'10px', 'display': 'inline-block'})
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
    q19_bar.update_yaxes(title_text="Count", title_font={"size": 12})
    q19_bar.update_xaxes(title_text="")
    q19_bar.update_layout(autosize=False, height=550, width=725, margin=dict(l=100), showlegend=False)
    q6_bar.update_yaxes(title_text="Count", title_font={"size": 12})
    q6_bar.update_xaxes(title_text="")
    q6_bar.update_layout(autosize=False, height=550, margin=dict(l=100), showlegend=False)
    q22_bar.update_yaxes(title_text="Count", title_font={"size": 12})
    q22_bar.update_xaxes(title_text="")
    q22_bar.update_layout(autosize=False, height=650, margin=dict(l=100), showlegend=False)
    return q2_pie, q23_bar, q19_bar, q6_bar, q22_bar

@app.callback(
    Output("shelter_map", "figure"),
    Input("shelter_year", "value"),
    Input("sector", "value")
)
def update_shelter_map(shelter_year,sector):
    # Shelter Occupancy Map
    months_to_use = list(month_dict.keys()) if shelter_year == None else list(month_dict.keys())[(shelter_year[0] - 1):shelter_year[-1]]
    #months_to_use = list(month_dict.keys())
    occ_sums = occupancy_[occupancy_['MONTH'].isin(months_to_use) & \
                          occupancy_['SECTOR'].isin(sector)] \
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
        title="Shelter Capacity in Greater Toronto Area (2020)",
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
    Input("sector", "value")
)
def update_shelter_trend(shelterClick,shelterSelect,shelter_year,sector):
    months_to_use = list(month_dict.keys()) if shelter_year == None else list(month_dict.keys())[(shelter_year[0] - 1):shelter_year[-1]]
    shelter_click = all_shelters if shelterClick == None else [find_shelter(point) for point in shelterClick["points"]]
    shelter_select = all_shelters if shelterSelect == None else [find_shelter(point) for point in shelterSelect["points"]]
    shelter_names = shelter_click if shelterSelect == None else shelter_select
    last_copy = shelter_names.copy() if ((shelterClick != None) or (shelterSelect!=None)) else all_shelters
    last_selection = last_copy if ((shelterClick == None) or (shelterSelect==None)) else shelter_names
    selected_sector = occupancy_[occupancy_['SHELTER_NAME'].isin(last_selection)]['SECTOR'].drop_duplicates().to_list()
    sector = list(set(sector+selected_sector)) if ((shelterClick != None) or (shelterSelect != None)) else all_sectors if len(sector)==0 else sector
    # Trend Charts
    sec_trend = occupancy_[occupancy_['MONTH'].isin(months_to_use) & \
                           occupancy_['SHELTER_NAME'].isin(last_selection) & \
                           occupancy_['SECTOR'].isin(sector)] \
        .groupby(["MONTH", "MONTH_NAME", "SECTOR"], as_index=False) \
        .agg({'OCCUPANCY': 'sum', 'CAPACITY': 'sum'})
    sec_trend['CAPACITY_PERC'] = sec_trend['OCCUPANCY'] / sec_trend['CAPACITY'] * 100
    sec_trend['WEIGHTED_CAP'] = sec_trend['CAPACITY_PERC'] * sec_trend['CAPACITY']
    sec_trend = sec_trend.sort_values(by='MONTH')
    sh_trend = occupancy_[occupancy_['MONTH'].isin(months_to_use) & \
                          occupancy_['SHELTER_NAME'].isin(last_selection) & \
                          occupancy_['SECTOR'].isin(sector)] \
        .groupby(["MONTH", "MONTH_NAME"] + loc_cols, as_index=False) \
        .agg({'OCCUPANCY': 'sum', 'CAPACITY': 'sum'})
    sh_trend['CAPACITY_PERC'] = sh_trend['OCCUPANCY'] / sh_trend['CAPACITY'] * 100
    sh_trend['WEIGHTED_CAP'] = sh_trend['CAPACITY_PERC'] * sh_trend['CAPACITY']
    sh_trend = sh_trend.sort_values(by='MONTH')
    sector_trend = px.line(sec_trend, x='MONTH', y='CAPACITY_PERC', color='SECTOR',
                           line_shape='spline',
                           range_y=[np.min(sec_trend['CAPACITY_PERC']) - 5, np.max(sec_trend['CAPACITY_PERC']) + 5],
                           title='Shelter Capacity By Sector (2020)')
    sector_trend.update_xaxes(title_text='Month',
                              ticktext=sec_trend['MONTH_NAME'],
                              tickvals=sec_trend['MONTH'])
    sector_trend.update_yaxes(title_text='Shelter Capacity (%)')
    sector_trend.update_layout(title_x=0.5,showlegend=False)
    shelter_trend = px.line(sh_trend, x='MONTH', y='CAPACITY_PERC', color='SHELTER_NAME',
                            line_shape='spline',
                            range_y=[np.min(sh_trend['CAPACITY_PERC']) - 5, np.max(sh_trend['CAPACITY_PERC']) + 5],
                            title='Shelter Capacity By Shelter (2020)')
    shelter_trend.update_xaxes(title_text='Month',
                               ticktext=sh_trend['MONTH_NAME'],
                               tickvals=sh_trend['MONTH'])
    shelter_trend.update_yaxes(title_text='Shelter Capacity (%)')
    shelter_trend.update_layout(title_x=0.5,showlegend=False)
    return sector_trend,shelter_trend


if __name__ == '__main__':
    app.run_server(debug=True)