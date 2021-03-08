# ======== Scrape site for data ======== #

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
import plotly
import dash_core_components as dcc
import dash_html_components as html

# Get data files
local_path = r'C:\Users\marke\Downloads\Datasets\Toronto_Homelessness'
sna_export = pd.read_csv(local_path+r'\sna2018opendata_export.csv').fillna(0)
sna_rows = pd.read_csv(local_path+r'\sna2018opendata_keyrows.csv')
sna_cols = pd.read_csv(local_path+r'\sna2018opendata_keycolumns.csv')
shelter_flow = pd.read_csv(local_path+r'\toronto-shelter-system-flow_march4.csv')
occupancy_curr = pd.read_csv(local_path+r'\Daily_shelter_occupancy_current.csv')
occupancy_2020 = pd.read_csv(local_path+r'\daily-shelter-occupancy-2020.csv')

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
plotly.offline.plot(q1_bar)

# Question 7: Have you stayed in an emergency shelter in the past 12 months?
q7 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION']=="Have you stayed in an emergency shelter in the past 12 months?")\
                   &(~sna_melt['RESPONSE'].isin(["Don’t know","Decline to answer"]))\
                   &(sna_melt['RESPONSE'].notnull()),]

q7_bar = px.bar(q7.loc[q7['GROUP'].isin(shelter_cols),],\
                 x="RESPONSE", y="COUNT", color="GROUP", \
                 title="Have you stayed in an emergency shelter in the past 12 months?",\
                 text='COUNT')
plotly.offline.plot(q7_bar)

# Question 22: What would help you find housing?
q22 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION']=="Please tell me which ones would help you personally find housing.")\
                   &(~sna_melt['RESPONSE'].isin(["Don't know","Decline to answer"]))\
                   &(sna_melt['RESPONSE'].notnull()),]

q22_bar = px.bar(q22.loc[q22['GROUP'].isin(shelter_cols),],\
                 x="RESPONSE", y="COUNT", color="GROUP", \
                 title="What would help you personally find housing?",\
                 text='COUNT')
plotly.offline.plot(q22_bar)

# Question 23: In the past 6 months, have you
q23 = sna_melt.loc[(sna_melt['QUESTION/CATEGORY DESCRIPTION'].str.contains("In the past 6 months, have you"))\
                   &(sna_melt['RESPONSE']=='Yes'),].drop("RESPONSE",axis=1)
q23['RESPONSE'] = q23['QUESTION/CATEGORY DESCRIPTION'].str[32:]

q23_bar = px.bar(q23.loc[q23['GROUP'].isin(shelter_cols),],\
                 x="RESPONSE", y="COUNT", color="GROUP", \
                 title="In the past 6 months, you have:",\
                 text='COUNT')
plotly.offline.plot(q23_bar)

################### Build Dash ###################
