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


# Get data files
#local_path = r'C:\Users\marke\Downloads\Datasets\Toronto_Homelessness'
local_path = r'/Users/merenberg/Desktop/dash-project/underlying_data'
sna_export = pd.read_csv(local_path+r'/sna2018opendata_export.csv').fillna(0)
sna_rows = pd.read_csv(local_path+r'/sna2018opendata_keyrows.csv')
sna_cols = pd.read_csv(local_path+r'/sna2018opendata_keycolumns.csv')
#shelter_flow = pd.read_csv(local_path+r'\toronto-shelter-system-flow_march4.csv')
#occupancy_curr = pd.read_csv(local_path+r'\Daily_shelter_occupancy_current.csv')
occupancy = pd.read_csv(local_path+r'/daily-shelter-occupancy-2020.csv')

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


################### Daily Shelter Occupancy ###################
ssl._create_default_https_context = ssl._create_unverified_context
nomi = pgeocode.Nominatim('ca')
post_col = 'SHELTER_POSTAL_CODE'

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
occupancy_['YEAR'] = occupancy_['OCCUPANCY_DATE'].apply(lambda x: int(x[6:]))

# Group by location (postal) and month of occupancy
occ_group = occupancy_.groupby(["MONTH","YEAR",post_col,'LATITUDE','LONGITUDE'])\
                      .agg({'OCCUPANCY':'mean','CAPACITY':'mean'}).reset_index()

# Example plot:
map = go.Figure()

map_dat = occ_group[occ_group['MONTH']==1]

map.add_trace(go.Scattermapbox(
        lat=map_dat['LATITUDE'],
        lon=map_dat['LONGITUDE'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=6,
            color='rgb(255, 0, 0)',
            opacity=0.7
        ),
        text=map_dat[post_col],
        hoverinfo='text')
)
'''
map.update_layout(
    title='Monthly',
    autosize=True,
    hovermode='closest',
    showlegend=False,
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=38,
            lon=-94
        ),
        pitch=0,
        zoom=3,
        style='light'
    ),
)
'''
#map.show()
plotly.offline.plot(map)


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
    Input("q1_bar","selectedData")
)
def update_group_in_figs(clickData,selectedData):
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


if __name__ == '__main__':
    app.run_server(debug=True)