import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go
import pandas as pd 
import numpy as np
#import dash_bootstrap_components as dbc
#from plotly.subplots import make_subplots
import io
import base64
import zipfile
from scipy.optimize import curve_fit
#from dash.exceptions import PreventUpdate
from utils.webpage_view import *
from utils.fitting_functions import *
import re
import scipy.stats as stats


''' -------------------------------------------- Table of Contents --------------------------------------------------

1) Preliminary -- Things required for the website to function properly (as intended)

2) Callbacks for Inputs -- Callbacks and functions defined for various kinds of inputs.

3) Display Data Tables -- based on the inputs the user gives.

4) Condtional display of radio buttons -- display radio buttons after the user selects a particular data set(s).

5) Main Functions -- Functions (and callbacks) for displaying graphs & model fitting, and for selected data sets (along with figures). '''



# ------------------------------------------------- 1) Preliminary stuff --------------------------------------------------

# Register the page name. If you change this, then you will have to change the name in home.py (href in id = go_to_database_btn)
dash.register_page(__name__,title='Search by Z and A',name='Search by Z and A')

# load the main log file.
df_NLD = pd.read_excel('log_book_new.xlsx')


# By default Plotly displays a blank plotting area on the webpage. This function is made to avoid displaying that once the webpage is loaded.

def blank_figure():
    '''Function to make a blank plotting area
    Inputs: None
    Output: a blank plotting area.'''

    fig = go.Figure(go.Scatter(x=[], y = []))
    fig.update_layout(template = None,paper_bgcolor='rgb(30,30,30)',plot_bgcolor='rgb(30,30,30)')
    fig.update_xaxes(showgrid = False, showticklabels = False, zeroline=False)
    fig.update_yaxes(showgrid = False, showticklabels = False, zeroline=False)
    
    return fig

# The layout of this webpage is described in utils/webpage_view.py
layout = html.Div(children=[
    dcc.Location(id='url'),
    html.Div(id='page-content'),
    dcc.Store(id='full-data-store',data=df_NLD.to_dict('records'))
])



# When a particular callback is triggered the corresponding function (below it) is executed. 
# This callback takes in the pathname of the database and outputs the webpage view.
@callback(
    Output('page-content','children'),
    [Input('url','pathname')]
    )
def display_page(pathname):
    '''Function to display the webpage.
    Input: the pathname (location) of the webpage.
    Output: The webpage view.'''

    out = view() # The webpage layout is stored in a function called view() in utils/webpage_view.py. The entire file is imported on Line 13.
    return out

# ------------------------------------------------- 2.0) Inputs for Z & A --------------------------------------------------

# Callback for first search criteria. Enter the proton number (Z) and it will show the mass numbers (A) that are available in the data set
# for that particular Z. 
# This is important so that the user can know what are their options once they select a Z.

@callback(
    Output('mass-number','options'),
    Input('proton-number','value')
)

def update_Z_dropdown(value):
    '''Function to display the mass numbers (A) associated with a selected proton number (Z).
    Input: value - proton number
    Output: The corresponding mass numbers.'''

    # Sort the mass numbers in ascending order using .sort_values(). The proton numbers are also arranged in ascending order (see utils/webpage_view.py)
    # There might be multiple datasets for same Z and A. We don't want that repititon to appear in the dropdown menu. Hence we use .unique()
    df_NLD.dropna(subset=['Datafile'],inplace=True)

    return df_NLD['A'][df_NLD['Z'] == value].sort_values().unique()


# ------------------------------------------------- 3.0) Display data table based on Z & A --------------------------------------------------

# Callback that takes in a particular Z, A and shows the available data sets with that Z and A.
# The allow_duplicate = True option, allows for the same output to be used in multiple callbacks.
# By default all callbacks are triggered one after the another. Setting prevent_initial_call = True 
# prevents certain callbacks to be triggered from the beginning.

@callback(
    [Output('data_log_table', 'data'),Output('full-data-store','data')],
    [Input('mass-number', 'value'),
     Input('proton-number', 'value'),
     Input('method_btn', 'value'),
     Input('search_by_reaction', 'value'),
     Input('status_btn', 'value')],
    prevent_initial_call=True
)
def update_table(A, Z, value_method, value_reaction, value_status):
    # Start with the full dataset
    filtered_df = df_NLD.copy()
    full_data_store = df_NLD.copy()

    
    # return nothing if nothing is chosen by the user.
    # if A is None or Z is None and value_method is None and value_reaction is None and value_status is None:
    #     return [],[]
    # Apply filters based on inputs if they are not None
    if A is not None and Z is not None:
        filtered_df = filtered_df[(filtered_df['A'] == A) & (filtered_df['Z'] == Z)]
        full_data_store = full_data_store[(full_data_store['A'] == A) & (full_data_store['Z'] ==Z)]
        
    
    if value_method:
        filtered_df = filtered_df[filtered_df['Method'].isin(value_method)]
        full_data_store = full_data_store[full_data_store['Method'].isin(value_method)]

    if value_reaction:
        value_reaction = re.sub(r'\s+|\(|\)', '', value_reaction).lower()
        filtered_df = filtered_df[filtered_df['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
        full_data_store = full_data_store[full_data_store['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]

    if value_status:
        filtered_df = filtered_df[filtered_df['Status'].isin(value_status)]
        full_data_store = full_data_store[full_data_store['Status'].isin(value_status)]

    # Drop unnecessary columns and return the data
    # filtered_df.dropna(subset=['Datafile'],inplace=True)
    # filtered_df =  filtered_df.reset_index()

    # full_data_store.dropna(subset=['Datafile'],inplace=True)
    # full_data_store =  full_data_store.reset_index()

    columns_to_hide = ['ID','Exrange','Datafile', 'Author','Distance','Status','Deformation']
    visible_df = filtered_df.drop(columns_to_hide, axis=1)
    
    return [visible_df.to_dict('records'),full_data_store.to_dict('records')]


# @callback(
#     [Output(component_id='data_log_table', component_property='data',allow_duplicate=True),Output('full-data-store','data',allow_duplicate=True)],
#     [Input(component_id='mass-number', component_property='value'),
#     Input(component_id='proton-number', component_property='value'),
#     Input('method_btn','value'),Input('search_by_reaction','value'),Input('status_btn','value')],prevent_initial_call=True
# )

# def update_table(A, Z,value_method,value_reaction,value_status):
#     '''Function to display the available datasets for a particular Z and A.
#     Inputs: A, Z - mass number, proton number.
#     Outputs: A slice of the data frame (data table) that has datasets available with that Z and A.'''

#     # dataframe (df) filtered by the user selected Z and A.

#     # if (value_method is None or len(value_method)==0) and (A is None or Z is None) and (value_reaction is None) or (value_status is None or len(value_status) == 0):
#     #     return [], []

    
#     filtered_df = df_NLD[(df_NLD['Z'] == Z) & (df_NLD['A'] == A)]
#     filtered_df.dropna(subset=['Datafile'],inplace=True)
#     filtered_df =  filtered_df.reset_index()

#     #filtered_df['Datafile'] = filtered_df['Datafile'].replace(np.nan,'File not available.')

#     # the original dataset has a lot of columns. We don't want to show all of them.
#     # Theses 3 columns -- ID (not useful info), Datafile (not useful info) & Author (mentioned in References) 
#     # -- were the ones that I didn't want to show on my webpage.
#     columns_to_hide = ['ID','Datafile','Author']

#     # hide those unnecessary columns.
#     visible_df = filtered_df.drop(columns_to_hide,axis=1)

    
#     # These dropped columns may not be useful for showing. But they will be useful for identifying which dataset was clicked (using ID)
#     # which datafile to retrieve (Datafile) and what to show in the legend of every plot (Author). 
#     # So, we will store the original, untampered data table as a seperate dataframe in the back such that it doesn't appear on the webpage.

#     full_data_store_filtered = df_NLD[(df_NLD['Z'] == Z) & (df_NLD['A'] == A)]
#     full_data_store_filtered.dropna(subset=['Datafile'],inplace=True)
#     full_data_store_filtered = full_data_store_filtered.reset_index()

#     print(value_method,value_status)

#     # if value_method is None or len(value_method)==0:
#     #     return [visible_df.to_dict('records'),full_data_store_filtered.to_dict('records')]

#     if (A and Z) and value_method:
#         filtered_df = df_NLD[(df_NLD['Z'] == Z) & (df_NLD['A'] == A)]
#         filtered_df.dropna(subset=['Datafile'],inplace=True)
#         filtered_df =  filtered_df.reset_index()
#         columns_to_hide = ['ID','Datafile','Author']

#         visible_df = filtered_df.drop(columns_to_hide,axis=1)
#         visible_df = visible_df[visible_df['Method'].isin(value_method)]
#         visible_df = visible_df.reset_index()

#         full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Method'].isin(value_method)]
#         full_data_store_filtered = full_data_store_filtered.reset_index()

#     if value_method and value_reaction:
#         value_reaction = re.sub(r'\s+|\(|\)', '', value_reaction).lower()
#         filtered_df = df_NLD[df_NLD['Method'].isin(value_method)]
#         filtered_df = filtered_df[filtered_df['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#         filtered_df.dropna(subset=['Datafile'],inplace=True)
#         filtered_df =  filtered_df.reset_index()
#         visible_df = filtered_df.drop(columns_to_hide,axis=1)

#         full_data_store_filtered = df_NLD[df_NLD['Method'].isin(value_method)]
#         full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#         full_data_store_filtered = full_data_store_filtered.reset_index()

#     if value_status is not None and value_method is not None:
#         filtered_df = df_NLD[(df_NLD['Method'].isin(value_method)) & (df_NLD['Status'].isin(value_status))]
#         #filtered_df = filtered_df[filtered_df['Status'].isin(value_status)]
#         filtered_df.dropna(subset=['Datafile'],inplace=True)
#         print(filtered_df.head())
#         filtered_df =  filtered_df.reset_index()
#         visible_df = filtered_df.drop(columns_to_hide,axis=1)
#         #visible_df = visible_df.reset_index()

#         full_data_store_filtered = df_NLD[df_NLD['Method'].isin(value_method)]
#         full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Status'].isin(value_status)]
#         full_data_store_filtered =  full_data_store_filtered.reset_index()

#     if (A or Z) and value_reaction:
#         value_reaction = re.sub(r'\s+|\(|\)', '', value_reaction).lower()

#         visible_df = visible_df[visible_df['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#         visible_df = visible_df.reset_index()

#         full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#         full_data_store_filtered = full_data_store_filtered.reset_index()

#     if (A or Z) and value_status:

#         visible_df = visible_df[visible_df['Status'].isin(value_status)]
#         visible_df = visible_df.reset_index()

#         full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Status'].isin(value_status)]
#         full_data_store_filtered = full_data_store_filtered.reset_index()

#     # if value_status and value_reaction:

#     #     value_reaction = re.sub(r'\s+|\(|\)', '', value_reaction).lower()

#     #     filtered_df = df_NLD[df_NLD['Status'].isin(value_status)]
#     #     filtered_df = filtered_df[filtered_df['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#     #     filtered_df =  filtered_df.reset_index()
#     #     visible_df = filtered_df.drop(columns_to_hide,axis=1)

#     #     full_data_store_filtered = df_NLD[df_NLD['Status'].isin(value_status)]
#     #     full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#     #     full_data_store_filtered =  full_data_store_filtered.reset_index()





#     # if value_method and value_reaction and (A or Z):

#     #     value_reaction = re.sub(r'\s+|\(|\)', '', value_reaction).lower()
#     #     visible_df = visible_df[visible_df['Method'].isin(value_method)]
#     #     visible_df = visible_df[visible_df['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#     #     visible_df = visible_df.reset_index()

#     #     full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Method'].isin(value_method)]
#     #     full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#     #     full_data_store_filtered = full_data_store_filtered.reset_index()

#     # if (A or Z) and value_reaction and value_status:

#     #     value_reaction = re.sub(r'\s+|\(|\)', '', value_reaction).lower()
#     #     visible_df = visible_df[visible_df['Status'].isin(value_status)]
#     #     visible_df = visible_df[visible_df['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#     #     visible_df = visible_df.reset_index()

#     #     full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Status'].isin(value_status)]
#     #     full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#     #     full_data_store_filtered = full_data_store_filtered.reset_index()

#     # if (A or Z) and value_method and value_status:

#     #     visible_df = visible_df[visible_df['Method'].isin(value_method)]
#     #     visible_df = visible_df[visible_df['Status'].isin(value_status)]
#     #     visible_df = visible_df.reset_index()

#     #     full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Method'].isin(value_method)]
#     #     full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Status'].isin(value_status)]
#     #     full_data_store_filtered.reset_index()

#     # if value_status and value_method and value_reaction:

#     #     value_reaction = re.sub(r'\s+|\(|\)', '', value_reaction).lower()

#     #     filtered_df = df_NLD[df_NLD['Status'].isin(value_status)]
#     #     filtered_df = filtered_df[filtered_df['Method'].isin(value_method)]
#     #     filtered_df = filtered_df[filtered_df['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
        
#     #     filtered_df =  filtered_df.reset_index()
#     #     visible_df = filtered_df.drop(columns_to_hide,axis=1)
#     #     visible_df = visible_df.reset_index()

#     #     full_data_store_filtered = df_NLD[df_NLD['Method'].isin(value_method)]
#     #     full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Status'].isin(value_status)]
#     #     full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#     #     full_data_store_filtered =  full_data_store_filtered.reset_index()


#     if value_method and (A is None and Z is None):
#         filtered_df = df_NLD[df_NLD['Method'].isin(value_method)]
#         filtered_df.dropna(subset=['Datafile'],inplace=True)
#         filtered_df =  filtered_df.reset_index()
#         visible_df = filtered_df.drop(columns_to_hide,axis=1)
#     # look at previous function's documentation to see why this was done.
#         columns_to_hide = ['ID','Datafile','Author']

#         visible_df = filtered_df.drop(columns_to_hide,axis=1)

#         full_data_store_filtered = df_NLD[df_NLD['Method'].isin(value_method)]
#         full_data_store_filtered.dropna(subset=['Datafile'],inplace=True)
#         full_data_store_filtered = full_data_store_filtered.reset_index()

    
    
#     if value_reaction and (A is None and Z is None):

#         value_reaction = re.sub(r'\s+|\(|\)', '', value_reaction).lower()

#         filtered_df = df_NLD[df_NLD['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#         filtered_df.dropna(subset=['Datafile'],inplace=True)
#         filtered_df =  filtered_df.reset_index()
#         columns_to_hide = ['ID','Datafile','Author']

#         visible_df = filtered_df.drop(columns_to_hide,axis=1)
#         visible_df = visible_df.reset_index()

#         full_data_store_filtered = df_NLD[df_NLD['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#         full_data_store_filtered.dropna(subset=['Datafile'],inplace=True)
#         full_data_store_filtered = full_data_store_filtered.reset_index()

#     if value_status and (A is None and Z is None):
#         filtered_df = df_NLD[df_NLD['Status'].isin(value_status)]
#         filtered_df.dropna(subset=['Datafile'],inplace=True)
#         filtered_df =  filtered_df.reset_index()
#         visible_df = filtered_df.drop(columns_to_hide,axis=1)
#     # look at previous function's documentation to see why this was done.
#         columns_to_hide = ['ID','Datafile','Author']

#         visible_df = filtered_df.drop(columns_to_hide,axis=1)
#         #visible_df = visible_df.reset_index()

#         full_data_store_filtered = df_NLD[df_NLD['Status'].isin(value_status)]
#         full_data_store_filtered.dropna(subset=['Datafile'],inplace=True)
#         full_data_store_filtered = full_data_store_filtered.reset_index()

#     # if value_method and value_reaction and value_status and (A or Z):

#     #     value_reaction = re.sub(r'\s+|\(|\)', '', value_reaction).lower()

#     #     visible_df = visible_df[visible_df['Status'].isin(value_status)]
#     #     visible_df = visible_df[visible_df['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#     #     visible_df = visible_df[visible_df['Method'].isin(value_method)]
#     #     visible_df = visible_df.reset_index()

#     #     full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Status'].isin(value_status)]
#     #     full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value_reaction])]
#     #     full_data_store_filtered = full_data_store_filtered[full_data_store_filtered['Method'].isin(value_method)]
#     #     full_data_store_filtered = full_data_store_filtered.reset_index()



    


#     return [visible_df.to_dict('records'),full_data_store_filtered.to_dict('records')]




# ------------------------------------------------- 3.1) Display data table based on method --------------------------------------------------

# Callback that takes in a particular method and shows the available data sets with that chosen method (e.g. Evaporation, Oslo, Ericson fluctuations etc.).
# The allow_duplicate = True option, allows for the same output to be used in multiple callbacks.
# By default all callbacks are triggered one after the another. Setting prevent_initial_call = True 
# prevents certain callbacks to be triggered from the beginning.

# @callback([Output('data_log_table','data',allow_duplicate=True),Output('full-data-store','data',allow_duplicate=True)],
#     [Input('method_btn','value')],[State('data_log_table','data')],prevent_initial_call=True)

# def update_table_method(value,data_log_table):

#     '''Function that displays the available datasets for a chosen method.
#     Inputs: value -- the chosen method(s). More than one method can be chosen.
#     Output: data table containing information about datasets with that chosen method(s).'''

#     # if no method (or methods) is chosen, return empty tables.

#     if value is None or len(value) == 0:
#         return data_log_table, data_log_table

#     # df filtered by the chosen methods.
#     filtered_df = df_NLD[df_NLD['Method'].isin(value)]
#     filtered_df.dropna(subset=['Datafile'],inplace=True)
#     filtered_df =  filtered_df.reset_index()

#     # look at previous function's documentation to see why this was done.
#     columns_to_hide = ['ID','Datafile','Author']

#     visible_df = filtered_df.drop(columns_to_hide,axis=1)

#     full_data_store_filtered = df_NLD[df_NLD['Method'].isin(value)]
#     full_data_store_filtered.dropna(subset=['Datafile'],inplace=True)
#     full_data_store_filtered = full_data_store_filtered.reset_index()
    

#     return [visible_df.to_dict('records'), full_data_store_filtered.to_dict('records')]


# ------------------------------------------------- 3.2) Display data table based on reaction --------------------------------------------------

# Callback that takes in a particular reaction and shows the available data sets with that chosen reaction.
# The allow_duplicate = True option, allows for the same output to be used in multiple callbacks.
# By default all callbacks are triggered one after the another. Setting prevent_initial_call = True 
# prevents certain callbacks to be triggered from the beginning.

# @callback([Output('data_log_table','data',allow_duplicate=True),Output('full-data-store','data',allow_duplicate=True)],
#     [Input('search_by_reaction','value')],prevent_initial_call=True)

# def update_table_reaction(value):

#     '''Function that displays the available datasets for a chosen reaction.
#     Inputs: value -- the chosen reaction. Only one reaction can be chosen.
#     Output: data table containing information about datasets with that reaction.'''

#     # If no reaction is chosen, return empty tables.
#     if value is None:
#         return [], []

#     value = re.sub(r'\s+|\(|\)', '', value).lower()

#     # Filter the dataframe by chosen reaction, after removing spaces, parentheses, and converting to lowercase
#     filtered_df = df_NLD[df_NLD['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value])]
#     filtered_df.dropna(subset=['Datafile'],inplace=True)
#     filtered_df =  filtered_df.reset_index()


#     columns_to_hide = ['ID','Datafile','Author']

#     visible_df = filtered_df.drop(columns_to_hide,axis=1)

#     full_data_store_filtered = df_NLD[df_NLD['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().isin([value])]
#     full_data_store_filtered.dropna(subset=['Datafile'],inplace=True)
#     full_data_store_filtered = full_data_store_filtered.reset_index()
    

#     return [visible_df.to_dict('records'), full_data_store_filtered.to_dict('records')]


# ------------------------------------------------- 3.3) Display data table based on status --------------------------------------------------

# Callback that displays the available data sets with a particular status (Accepted, Rejected or Probation).
# By default all callbacks are triggered one after the another. Setting prevent_initial_call = True 
# prevents certain callbacks to be triggered from the beginning.

# @callback([Output('data_log_table','data'),Output('full-data-store','data')],
#     [Input('status_btn','value')],prevent_initial_call=True)

# def update_table_status(value):

#     '''Function that displays the available datasets for a chosen status.
#     Inputs: value -- the chosen status. More than one status can be chosen.
#     Output: data table containing information about datasets with that status.'''

#     # If no status is chosen, return empty tables.
#     if value is None:
#         return [],[]

#     # filter the data table by the status (Accepted, Rejected or Probation).
#     filtered_df = df_NLD[df_NLD['Status'].isin(value)]
#     filtered_df.dropna(subset=['Datafile'],inplace=True)
#     filtered_df =  filtered_df.reset_index()

#     columns_to_hide = ['ID','Datafile','Author']

#     visible_df = filtered_df.drop(columns_to_hide,axis=1)

#     full_data_store_filtered = df_NLD[df_NLD['Status'].isin(value)]
#     full_data_store_filtered.dropna(subset=['Datafile'],inplace=True)
#     full_data_store_filtered = full_data_store_filtered.reset_index()
    

#     return [visible_df.to_dict('records'), full_data_store_filtered.to_dict('records')]


# ------------------------------------------------- 4) Display radio buttons after data selection --------------------------------------------------

# callbacks to show the radio buttons after data has been selected.
@callback(
    Output('radio_btn','style'),
    Input('data_log_table','derived_virtual_selected_rows'))


def trigger_log_btn(selected_data):
    '''Function to show the Log/Linear button after any data has been selected.
    This function was put in for 2 reasons -- 1) To give the website a clean look 
    2) To make things appear when they are needed. In this case, we do not need the Log/Linear scale button
    until data has been selected and a graph is shown.

    INPUTS: selected_data -- self-explanatory :)
    OUTPUTS: The Log/Linear scaling buttons.'''

    if selected_data:
        # display the radio buttons in block style.
        return {'display': 'block'}

    else:

        return {'display': 'none'}



@callback(
    Output('radio_btn_fitting','style'),
    Input('data_log_table','derived_virtual_selected_rows'))


def trigger_fit_btn(selected_data):
    '''Function to show the model fitting button after any data has been selected.
    This function was put in for 2 reasons -- 1) To give the website a clean look 
    2) To make things appear when they are needed. In this case, we do not need the model fitting buttons
    until data has been selected and a graph is shown.

    INPUTS: selected_data -- self-explanatory :)
    OUTPUTS: The model fitting buttons.'''

    if selected_data:

        return {'display': 'block'}

    else:

        return {'display': 'none'}

@callback(
    Output('split_unsplit_btn','style'),
    Input('data_log_table','derived_virtual_selected_rows'),prevent_initial_call=True)


def trigger_split_btn(selected_data):
    '''By default, all the selected data sets are shown on 1 plot. So, I added a Split/Unsplit functionality
    if the user wants to see the data sets plotted in different figures (1 dataset per figure).
    This function shows the Split/Unsplit button after at least 2 data sets have been selected (doesn't make sense to split 1 dataset :)).

    INPUTS: selected_data -- self-explanatory :)
    OUTPUTS: The Split/Unsplit button.'''

    if len(selected_data) > 1:

        return {'display': 'block'}

    else:

        return {'display': 'none'}

# ---------------------------------------------------- 5) Main Functions ------------------------------------

# callback to display the figures and the fits
# Input 1: selected data sets from data table -- Input('data_log_table','derived_virtual_selected_rows')
# Input 2: whether you want to see the data in Log scale or Linear scale -- Input('radio_btn','value') -- default is linear scale
# Input 3: To which model (CT or BSFG or both) would you like to fit the data -- Input('radio_btn_fitting','value') -- default is none
# Input 4: whether you want to see the plots in Split/Unsplit version -- Input('split_unsplit_btn','n_clicks')
# State takes any output from previous callbacks and keeps it (without changing it) -- store the full log of the available data sets.
# Output: graphs of level densities.

@callback(
    Output('div-graphs', 'children'),
    [Input('data_log_table','derived_virtual_selected_rows'),Input('radio_btn','value'),Input('radio_btn_fitting','value'),
    Input('split_unsplit_btn','n_clicks')],
    State('full-data-store','data'),prevent_initial_call=True)


def plot_selected_data(derived_virtual_selected_rows,value,value_fit,n_clicks,data):
    '''Function to display plots of level density data sets based on user selection.
    Inputs: user selected data sets, choice of linear/log scale, choice of fitting model(s), 
    checkpoint to see if Split/Unsplit button was clicked, full data store.
    Outputs: Plots of level density data (in split or unsplit version).'''

    # blank_figure() function was defined at the beginning of this document.
    fig = blank_figure()

    # a list to store the splitted plots.
    split_plots = []
    
    # If and only if the user selects some data set in the table
    if derived_virtual_selected_rows and data:

        # by default all plots are unsplit. By default, n_clicks value has been set to 0 (even). 
        #So, if n_clicks (number of clicks on the split/unsplit button) is an odd integer, that would mean 
        # the program needs to split the plots.
        split = (n_clicks % 2 == 1) 

        # convert dictionary to pandas dataframe.
        data_df = pd.DataFrame.from_dict(data)
        graphs = []

        # if the user selects to split the graphs
        if split:

            # extract information about the nucleus from the selected rows.
            for i in derived_virtual_selected_rows:
                fig = blank_figure()
                Z = data_df['Z'][i]
                A = data_df['A'][i]
                datafile = data_df['Datafile'][i]

                # minimum and maximum energy of fitting.
                E_min = data_df['Emin'][i]
                E_max = data_df['Emax'][i]

                # location of csv data file.
                #file_loc = '../OhioUniversity/PhD/NLDD/data_sets/' + datafile
                nld_data = pd.read_csv(datafile,header=None,sep=',',comment='#')

                unnamed_cols = nld_data.filter(like='3').columns
                if not unnamed_cols.empty:
                    nld_data.drop(columns=unnamed_cols, inplace=True)

                #nld_data.drop(3, axis=1, inplace=True)
                nld_data.rename(columns={0: "E (MeV)", 1: "NLD", 2: "NLD uncertainity"}, inplace=True)

                fig.add_trace(go.Scatter(x=nld_data['E (MeV)'],y=nld_data['NLD'],error_y=dict(type='data',array=nld_data['NLD uncertainity']),mode='markers',
                    name=data_df['Author'][i],showlegend=True))

                fig.update_xaxes(showline=True,linecolor='orange',color='orange',title_font_color='orange', linewidth=2,mirror=True,
                    showgrid=True,gridcolor='LightGray',showticklabels=True, title_text='E (MeV)')

                if value == 'log':

                    fig.update_yaxes(showline=True,type="log", linecolor='orange',color='orange',title_font_color='orange', linewidth=2,mirror=True,
                    tickformat=".2e",dtick=0.5,showgrid=True,gridcolor='LightGray',showticklabels=True,title_text='NLD (1/MeV)')

                else:

                    fig.update_yaxes(showline=True,linecolor='orange',color='orange',title_font_color='orange', linewidth=2,mirror=True,
                    showgrid=True,gridcolor='LightGray',showticklabels=True,tickformat=".2e",title_text='NLD (1/MeV)')

                fig.update_layout(legend_font_color='white') # setting legend font color
                
                # fit the data according to the model(s) the user selects. 
                if value_fit == 'CTM':

                    nld_data_fit = nld_data[(nld_data['E (MeV)'] > E_min) & (nld_data['E (MeV)'] < E_max+0.1)]

                    x,y,dy = nld_data_fit['E (MeV)'],nld_data_fit['NLD'],nld_data_fit['NLD uncertainity']

                    dy = np.where(dy == 0, 0.2*y, dy)
               
                    popt, pcov = curve_fit(ctm_fitting, xdata=x,ydata=y,sigma=dy,absolute_sigma=True)

                    x_fit = np.linspace(E_min, E_max,100)

                    y_fit = ctm_fitting(x_fit, *popt)

                    param_errors = np.sqrt(np.diag(pcov))

                    # alpha = 0.05

                    # n_params = len(popt)

                    # t_value = stats.t.ppf(1 - alpha/2, df=len(x_fit) - n_params)

                    # y_lower = ctm_fitting(x_fit, *(popt - t_value * param_errors))
                    # y_upper = ctm_fitting(x_fit, *(popt + t_value * param_errors))


                    fig.add_trace(go.Scatter(x=x_fit,y=y_fit,mode='lines',
                        name='T = {}, E = {}, <br> dT = {}, dE = {}'.format(np.round(popt[0],2),np.round(popt[1],2),np.round(param_errors[0],2),
                        np.round(param_errors[1],2))))

                    # fig.add_trace(go.Scatter(x=x_fit, y=y_upper, mode='lines', fill=None,line=dict(dash='dash'), 
                    # showlegend=False))

                    # fig.add_trace(go.Scatter(x=x_fit, y=y_lower, mode='lines', fill='tonexty',line=dict(dash='dash'),
                    # showlegend=False))

                elif value_fit == 'BSFG':

                    nld_data_fit = nld_data[(nld_data['E (MeV)'] > E_min) & (nld_data['E (MeV)'] < E_max+0.1)]

                    x,y,dy = nld_data_fit['E (MeV)'],nld_data_fit['NLD'],nld_data_fit['NLD uncertainity']

                    dy = np.where(dy == 0, 0.2*y, dy)
               
                    popt, pcov = curve_fit(lambda E, a, Delta: bsfg_fitting(E,a,Delta,A), xdata=x,ydata=y,sigma=dy,absolute_sigma=True)
                    

                    x_fit = np.linspace(E_min, E_max,100)

                    y_fit = bsfg_fitting(x_fit,*popt,A)

                    param_errors = np.sqrt(np.diag(pcov))

                    # alpha = 0.05

                    # n_params = len(popt)

                    # t_value = stats.t.ppf(1 - alpha/2, df=len(x_fit) - n_params)

                    # y_lower = bsfg_fitting(x_fit, *(popt - t_value * param_errors))
                    # y_upper = bsfg_fitting(x_fit, *(popt + t_value * param_errors))


                    fig.add_trace(go.Scatter(x=x_fit,y=y_fit,mode='lines',
                        name='a = {}, del = {}, <br> da = {}, ddel = {}'.format(np.round(popt[0],2),np.round(popt[1],2),np.round(param_errors[0],2),
                        np.round(param_errors[1],2))))

                    # fig.add_trace(go.Scatter(x=x_fit, y=y_upper, mode='lines', fill=None,line=dict(dash='dash'), 
                    #     showlegend=False))

                    # fig.add_trace(go.Scatter(x=x_fit, y=y_lower, mode='lines', fill='tonexty',line=dict(dash='dash'),
                    # showlegend=False))


                elif value_fit == 'All':

                    nld_data_fit = nld_data[(nld_data['E (MeV)'] > E_min) & (nld_data['E (MeV)'] < E_max+0.1)]

                    x,y,dy = nld_data_fit['E (MeV)'],nld_data_fit['NLD'],nld_data_fit['NLD uncertainity']

                    dy = np.where(dy == 0, 0.2*y, dy)
               
                    popt_bsfg, pcov_bsfg = curve_fit(lambda E, a, Delta: bsfg_fitting(E,a,Delta,A), xdata=x,ydata=y,sigma=dy,absolute_sigma=True)

                    x_fit = np.linspace(E_min, E_max,100)

                    y_fit_bsfg = bsfg_fitting(x_fit, *popt_bsfg,A)

                    param_errors_bsfg = np.sqrt(np.diag(pcov_bsfg))

                    # alpha = 0.05

                    # n_params_bsfg = len(popt_bsfg)

                    # t_value_bsfg = stats.t.ppf(1 - alpha/2, df=len(x_fit) - n_params_bsfg)

                    # y_lower_bsfg = bsfg_fitting(x_fit, *(popt_bsfg - t_value_bsfg * param_errors_bsfg))
                    # y_upper_bsfg = bsfg_fitting(x_fit, *(popt_bsfg + t_value_bsfg * param_errors_bsfg))


                    fig.add_trace(go.Scatter(x=x_fit,y=y_fit_bsfg,mode='lines',
                        name='a = {}, del = {}, <br> da = {}, ddel = {}'.format(np.round(popt_bsfg[0],2),np.round(popt_bsfg[1],2),
                        np.round(param_errors_bsfg[0],2),np.round(param_errors_bsfg[1],2))))

                    # fig.add_trace(go.Scatter(x=x_fit, y=y_upper_bsfg, mode='lines', fill=None,line=dict(dash='dash'), 
                    # showlegend=False))

                    # fig.add_trace(go.Scatter(x=x_fit, y=y_lower_bsfg, mode='lines', fill='tonexty',line=dict(dash='dash'),
                    # showlegend=False))

                    popt_ctm, pcov_ctm = curve_fit(ctm_fitting, xdata=x,ydata=y,sigma=dy,absolute_sigma=True)

                    x_fit = np.linspace(E_min, E_max,100)

                    y_fit_ctm = ctm_fitting(x_fit, *popt_ctm)

                    param_errors_ctm = np.sqrt(np.diag(pcov_ctm))

                    # alpha = 0.05

                    # n_params_ctm = len(popt_ctm)

                    # t_value_ctm = stats.t.ppf(1 - alpha/2, df=len(x_fit) - n_params_ctm)

                    # y_lower_ctm = ctm_fitting(x_fit, *(popt_ctm - t_value_ctm * param_errors_ctm))
                    # y_upper_ctm = ctm_fitting(x_fit, *(popt_ctm + t_value_ctm * param_errors_ctm))


                    fig.add_trace(go.Scatter(x=x_fit,y=y_fit_ctm,mode='lines',
                        name='T = {}, E = {}, <br> dT = {}, dE = {}'.format(np.round(popt_ctm[0],2),np.round(popt_ctm[1],2),
                        np.round(param_errors_ctm[0],2),np.round(param_errors_ctm[1],2))))

                    # fig.add_trace(go.Scatter(x=x_fit, y=y_upper_ctm, mode='lines', fill=None,line=dict(dash='dash'), 
                    # showlegend=False))

                    # fig.add_trace(go.Scatter(x=x_fit, y=y_lower_ctm, mode='lines', fill='tonexty',line=dict(dash='dash'),
                    # showlegend=False))


                graphs.append(html.Div([dcc.Graph(figure=fig)], className='graph-item'))
                

            return html.Div(graphs,className='graph-grid')


        #data_df = pd.DataFrame.from_dict(data)

        
        # if the user doesn't opt to split the plots, then
        for i in derived_virtual_selected_rows:

            fig.update_layout(autosize=True,
            paper_bgcolor='rgb(30,30,30)', # Background color of the entire plot area
            plot_bgcolor='rgb(30,30,30)',  # Background color of the plotting area
            showlegend=True,                   # Show the legend
            legend_font_color='white',legend_font_size=14,
            xaxis=dict(showline=True, linewidth=2, linecolor='orange', mirror=True), # X-axis line styling
            yaxis=dict(showline=True, linewidth=2, linecolor='orange', mirror=True),  # Y-axis line styling
            
        )
            
            Z = data_df['Z'][i]
            A = data_df['A'][i]
            datafile = data_df['Datafile'][i]
            
            E_min = data_df['Emin'][i]
            E_max = data_df['Emax'][i]

            
            #file_loc = '../OhioUniversity/PhD/NLDD/data_sets/' + datafile

            nld_data = pd.read_csv(datafile,header=None,sep=',',comment='#')

            unnamed_cols = nld_data.filter(like='3').columns
            if not unnamed_cols.empty:
                nld_data.drop(columns=unnamed_cols, inplace=True)

            #nld_data.drop(3, axis=1, inplace=True)
            # renaming columns
            nld_data.rename(columns={0: "E (MeV)", 1: "NLD", 2: "NLD uncertainity"}, inplace=True)

            fig.add_trace(go.Scatter(x=nld_data['E (MeV)'],y=nld_data['NLD'],error_y=dict(type='data',array=nld_data['NLD uncertainity']),mode='markers',
                    name=data_df['Author'][i]))

            fig.update_xaxes(showline=True,linecolor='orange',color='orange',title_font_color='orange', linewidth=2,mirror=True,
                    showgrid=True,gridcolor='LightGray',showticklabels=True,title_text='E (MeV)')

            #convert y-axis to log scale if the user selects to view in log scale.
            if value == 'log':

                fig.update_yaxes(showline=True,type="log", linecolor='orange',color='orange',title_font_color='orange', linewidth=2,mirror=True,
                    tickformat=".2e",dtick=0.5,showgrid=True,gridcolor='LightGray',showticklabels=True,title_text='NLD (1/MeV)')

            else:

                fig.update_yaxes(showline=True,linecolor='orange',color='orange',title_font_color='orange',linewidth=2,mirror=True,
                    showgrid=True,gridcolor='LightGray',tickformat=".2e",showticklabels=True,title_text='NLD (1/MeV)')

                
            # Fitting data in unsplit mode.

            if value_fit == 'CTM':

                nld_data_fit = nld_data[(nld_data['E (MeV)'] > E_min) & (nld_data['E (MeV)'] < E_max+0.1)]

                x,y,dy = nld_data_fit['E (MeV)'],nld_data_fit['NLD'],nld_data_fit['NLD uncertainity']

                dy = np.where(dy == 0, 0.2*y, dy)
               
                popt, pcov = curve_fit(ctm_fitting, xdata=x,ydata=y,sigma=dy,absolute_sigma=True)

                x_fit = np.linspace(E_min, E_max,100)

                y_fit = ctm_fitting(x_fit, *popt)

                param_errors = np.sqrt(np.diag(pcov))

                # alpha = 0.05

                # n_params = len(popt)

                # t_value = stats.t.ppf(1 - alpha/2, df=len(x_fit) - n_params)

                # y_lower = ctm_fitting(x_fit, *(popt - t_value * param_errors))
                # y_upper = ctm_fitting(x_fit, *(popt + t_value * param_errors))


                fig.add_trace(go.Scatter(x=x_fit,y=y_fit,mode='lines',
                    name='T = {}, E = {}, <br> dT = {}, dE = {}'.format(np.round(popt[0],2),np.round(popt[1],2),np.round(param_errors[0],2),
                        np.round(param_errors[1],2))))

                # fig.add_trace(go.Scatter(x=x_fit, y=y_upper, mode='lines', fill=None,line=dict(dash='dash'), 
                #     showlegend=False))

                # fig.add_trace(go.Scatter(x=x_fit, y=y_lower, mode='lines', fill='tonexty',line=dict(dash='dash'),
                #  showlegend=False))

            elif value_fit == 'BSFG':

                nld_data_fit = nld_data[(nld_data['E (MeV)'] > E_min) & (nld_data['E (MeV)'] < E_max+0.1)]

                x,y,dy = nld_data_fit['E (MeV)'],nld_data_fit['NLD'],nld_data_fit['NLD uncertainity']
                
                dy = np.where(dy == 0, 0.2*y, dy)
                #lower_bound = [1e-6,-np.inf]
                #upper_bound = [np.inf, np.inf]
                popt, pcov = curve_fit(lambda E, a, Delta: bsfg_fitting(E,a,Delta,A), xdata=x,ydata=y,sigma=dy,absolute_sigma=True)

                x_fit = np.linspace(E_min, E_max,100)

                y_fit = bsfg_fitting(x_fit, *popt,A)

                param_errors = np.sqrt(np.diag(pcov))

                # alpha = 0.05

                # n_params = len(popt)

                # t_value = stats.t.ppf(1 - alpha/2, df=len(x_fit) - n_params)

                # y_lower = bsfg_fitting(x_fit, *(popt - t_value * param_errors))
                # y_upper = bsfg_fitting(x_fit, *(popt + t_value * param_errors))


                fig.add_trace(go.Scatter(x=x_fit,y=y_fit,mode='lines',
                    name='a = {}, del = {}, <br> da = {}, ddel = {}'.format(np.round(popt[0],2),np.round(popt[1],2),np.round(param_errors[0],2),
                        np.round(param_errors[1],2))))

                # fig.add_trace(go.Scatter(x=x_fit, y=y_upper, mode='lines', fill=None,line=dict(dash='dash'), 
                #     showlegend=False))

                # fig.add_trace(go.Scatter(x=x_fit, y=y_lower, mode='lines', fill='tonexty',line=dict(dash='dash'),
                #  showlegend=False))

            elif value_fit == 'All':

                nld_data_fit = nld_data[(nld_data['E (MeV)'] > E_min) & (nld_data['E (MeV)'] < E_max+0.1)]

                x,y,dy = nld_data_fit['E (MeV)'],nld_data_fit['NLD'],nld_data_fit['NLD uncertainity']

                dy = np.where(dy == 0, 0.2*y, dy)
                
                popt_bsfg, pcov_bsfg = curve_fit(lambda E, a, Delta: bsfg_fitting(E,a,Delta,A), xdata=x,ydata=y,sigma=dy,absolute_sigma=True)

                x_fit = np.linspace(E_min, E_max,100)

                y_fit_bsfg = bsfg_fitting(x_fit, *popt_bsfg,A)

                param_errors_bsfg = np.sqrt(np.diag(pcov_bsfg))

                # alpha = 0.05

                # n_params_bsfg = len(popt_bsfg)

                # t_value_bsfg = stats.t.ppf(1 - alpha/2, df=len(x_fit) - n_params_bsfg)

                # y_lower_bsfg = bsfg_fitting(x_fit, *(popt_bsfg - t_value_bsfg * param_errors_bsfg))
                # y_upper_bsfg = bsfg_fitting(x_fit, *(popt_bsfg + t_value_bsfg * param_errors_bsfg))


                fig.add_trace(go.Scatter(x=x_fit,y=y_fit_bsfg,mode='lines',
                    name='a = {}, del = {}, <br> da = {}, ddel = {}'.format(np.round(popt_bsfg[0],2),np.round(popt_bsfg[1],2),
                        np.round(param_errors_bsfg[0],2),np.round(param_errors_bsfg[1],2))))

                # fig.add_trace(go.Scatter(x=x_fit, y=y_upper_bsfg, mode='lines', fill=None,line=dict(dash='dash'), 
                #     showlegend=False))

                # fig.add_trace(go.Scatter(x=x_fit, y=y_lower_bsfg, mode='lines', fill='tonexty',line=dict(dash='dash'),
                #  showlegend=False))


                popt_ctm, pcov_ctm = curve_fit(ctm_fitting, xdata=x,ydata=y,sigma=dy,absolute_sigma=True)

                x_fit = np.linspace(E_min, E_max,100)

                y_fit_ctm = ctm_fitting(x_fit, *popt_ctm)

                param_errors_ctm = np.sqrt(np.diag(pcov_ctm))

                # alpha = 0.05

                # n_params_ctm = len(popt_ctm)

                # t_value_ctm = stats.t.ppf(1 - alpha/2, df=len(x_fit) - n_params_ctm)

                # y_lower_ctm = ctm_fitting(x_fit, *(popt_ctm - t_value_ctm * param_errors_ctm))
                # y_upper_ctm = ctm_fitting(x_fit, *(popt_ctm + t_value_ctm * param_errors_ctm))


                fig.add_trace(go.Scatter(x=x_fit,y=y_fit_ctm,mode='lines',
                    name='T = {}, E = {},<br> dT = {}, dE = {}'.format(np.round(popt_ctm[0],2),np.round(popt_ctm[1],2),
                        np.round(param_errors_ctm[0],2),np.round(param_errors_ctm[1],2))))

                # fig.add_trace(go.Scatter(x=x_fit, y=y_upper_ctm, mode='lines', fill=None,line=dict(dash='dash'), 
                #     showlegend=False))

                # fig.add_trace(go.Scatter(x=x_fit, y=y_lower_ctm, mode='lines', fill='tonexty',line=dict(dash='dash'),
                #  showlegend=False))


            split_plots.append(dcc.Graph(id=f'graph-{i}',figure=fig))
          
    return [dcc.Graph(id='graph',figure=fig,style={"width":"100%","height":"100vh"})]




@callback(
    Output("download-data", "data"),
    [Input("download_btn", "n_clicks")],
    [State('data_log_table', 'derived_virtual_selected_rows'), State('full-data-store', 'data'),
     State('div-graphs', 'children'),State('split_unsplit_btn','n_clicks')]
)
def create_zip(n_clicks_download,selected_rows, data, div_graphs_children,n_clicks_split):

    if n_clicks_download is None or not selected_rows:
        return dash.no_update

    unsplit = (n_clicks_split % 2 == 0)


    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        data_df = pd.DataFrame.from_dict(data)
        selected_df = data_df.iloc[selected_rows]
        selected_data_sets = selected_df['Datafile']

        for ind,i in enumerate(selected_rows):
            csv_data_set = pd.read_csv(selected_data_sets[i],comment='#',header=None)
            csv_data_set.rename(columns={0: "E (MeV)", 1: "NLD", 2: "NLD uncertainity"}, inplace=True)

            unnamed_cols = csv_data_set.filter(like='3').columns
            if not unnamed_cols.empty:
                csv_data_set.drop(columns=unnamed_cols, inplace=True)

            csv_data_bytes = csv_data_set.to_csv(index=False)
            zf.writestr("selected_data_{}.csv".format(ind), csv_data_bytes)

            if not unsplit:

                figure = div_graphs_children['props']['children'][ind]['props']['children'][0]['props']['figure']
                fig = go.Figure(figure)
                # Write the image to the buffer
                image_data = io.BytesIO()
                fig.write_image(image_data, format='png')
                image_data.seek(0)
                zf.writestr(f"figure_{ind}.png", image_data.read())

        
        if unsplit: 
            for child in div_graphs_children:
                if 'props' in child and 'figure' in child['props']:
                    figure = child['props']['figure']
                    fig = go.Figure(figure)

                    # Write the image to the buffer
                    image_data = io.BytesIO()
                    fig.write_image(image_data, format='png')
                    image_data.seek(0)
                    zf.writestr("figure.png", image_data.read())
                    break
        
                
                
    buffer.seek(0)
    encoded_zip = base64.b64encode(buffer.read()).decode("utf-8")
    return dict(content=encoded_zip, filename="download.zip", base64=True)
