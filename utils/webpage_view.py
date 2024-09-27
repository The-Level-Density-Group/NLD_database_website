from dash import dcc,dash_table
from dash import html
import pandas as pd 
import dash_bootstrap_components as dbc


df_NLD = pd.read_excel('log_book_new.xlsx')

def view():
    return \
    html.Div(id="body", className="container scalable", children=[
        html.A(html.H1('The Level Density Project',className='website_header_database'),href='/',className='header_banner_link_database'),
        html.Hr(id='banner_hr'),
        html.Div(id="app-container", children=[
            html.Div(id="left-column", children=[
                html.P('Search Criteria:',id='search_criteria_header'),
                dcc.Dropdown(df_NLD['Z'].sort_values().unique(), id='proton-number', value=None, className="input1", placeholder='Enter Proton Number'),
                dcc.Dropdown(id='mass-number', value=None, className="input2", placeholder='Enter Mass Number'),

                html.Hr(id='criteria_hr'),

                html.P('Filter by method:',id='method_filter_header'),
                html.Div(dbc.Checklist(options=[{"label": "Evaporation", "value": 'Evaporation'},{"label": "Oslo", "value":'Oslo'},
                    {"label": "Ericson", "value":'Ericson'},{"label": "Inverse Oslo", "value":'Inverse Oslo'},{"label": "Beta-p", "value":'Beta-p'},
                    {"label": "Beta-n", "value":'Beta-n'},{"label": "Beta Oslo", "value":'Beta Oslo'},],
                    id="method_btn",inline=True,switch=True),className='method-btn'),

                html.Div(dbc.Input(id='search_by_reaction',type='text',placeholder='Search by Reaction')),

                html.Div(dbc.Checklist(options=[{"label": "Recommended", "value": 'Accepted'},{"label": "Not Recommended", "value":'Rejected'},
                    {'label':'Under Review','value':'Probation'}],id="status_btn",inline=True,switch=True),className='status-btn'),

                html.Div([html.Button('Download CSV', id='download_btn', className="button1"),
                    dcc.Download(id="download-data")],className='download-btn-class'),

                
                html.Div(html.Button('Split/Unsplit plots', id='split_unsplit_btn', className="button2",n_clicks=0)),

                
            ]),

            html.Div(id='center-column', children=[html.Div([dash_table.DataTable(data=[],id='data_log_table',row_selectable='multi',
                style_table={'width': '100%','overflowX':'auto'},

                style_header={'backgroundColor': 'rgb(30,30,30)','color': 'orange','border':'2px solid white'},
                    style_data={'backgroundColor': 'rgb(50,50,50)','color': 'orange','border':'2px solid white'},
                    page_size=10,
                    )]),

                html.Div([dash_table.DataTable(data=[],id='selected_data',row_selectable='multi', 
                    style_table={'width': '100%','borderRadius': '5px','overflowX':'auto'},
                    style_header={'backgroundColor': 'rgb(30,30,30)','color': 'orange','border':'2px solid orange'},
                    style_data={'backgroundColor': 'rgb(50,50,50)','color': 'orange','border':'2px solid orange'},)],className='datatable'),
                

                html.Div(dbc.RadioItems(options=[{"label": "Log", "value": 'log'},{"label": "Linear", "value":'linear'},],
            value='linear',id="radio_btn",inline=True,switch=True),className='scaling-btn'),

                html.Div(dbc.RadioItems(options=[{'label':'CT Model','value':'CTM'},{'label':'BSFG Model','value':'BSFG'},
                    {'label':'All Models','value':'All'}],
        id='radio_btn_fitting',inline=True),className='radio-btn-fitting-container'),

                dcc.Loading(children=[
                    html.Div(id="div-graphs")
                ])
            ]),                   
        ]),
    ]),


