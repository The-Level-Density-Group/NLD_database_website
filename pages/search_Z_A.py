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


''' -------------------------------------------- Table of Contents --------------------------------------------------

1) Preliminary -- Things required for the website to function properly (as intended)

2) Condtional display of radio buttons -- display radio buttons after the user selects a particular data set(s).

3) Main Functions -- Functions (and callbacks) for displaying graphs & model fitting, and for selected data sets (along with figures). '''



# ------------------------------------------------- 1) Preliminary stuff --------------------------------------------------

# Register the page name. If you change this, then you will have to change the name in home.py (href in id = go_to_database_btn)
dash.register_page(__name__,title='Search by Z and A',name='Search by Z and A')

# load the main log file.
df_NLD = pd.read_excel('log_book_new.xlsx')
df_NLD.dropna(subset=['Datafile'],inplace=True)

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
        filtered_df = filtered_df[filtered_df['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().str.contains(value_reaction,na=False)]
        full_data_store = full_data_store[full_data_store['Reaction'].str.replace(r'\s+|\(|\)', '', regex=True).str.lower().str.contains(value_reaction,na=False)]

    if value_status:
        filtered_df = filtered_df[filtered_df['Status'].isin(value_status)]
        full_data_store = full_data_store[full_data_store['Status'].isin(value_status)]

    # Drop unnecessary columns and return the data
    # filtered_df.dropna(subset=['Datafile'],inplace=True)
    # filtered_df =  filtered_df.reset_index()

    # full_data_store.dropna(subset=['Datafile'],inplace=True)
    # full_data_store =  full_data_store.reset_index()

    columns_to_hide = ['ID','Exrange','Datafile', 'Author','Distance','Status','Deformation','Comments']
    visible_df = filtered_df.drop(columns_to_hide, axis=1)
    
    return [visible_df.to_dict('records'),full_data_store.to_dict('records')]


# ------------------------------------------------- 2) Display radio buttons after data selection --------------------------------------------------

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

# ---------------------------------------------------- 3) Main Functions ------------------------------------

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
                    name=f"{data_df['Author'][i]} - {data_df['Isotope'][i]}",showlegend=True))

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


                    fig.add_trace(go.Scatter(x=x_fit,y=y_fit,mode='lines',
                        name='T = {}, E = {}, <br> dT = {}, dE = {}'.format(np.round(popt[0],2),np.round(popt[1],2),np.round(param_errors[0],2),
                        np.round(param_errors[1],2))))

                    

                elif value_fit == 'BSFG':

                    nld_data_fit = nld_data[(nld_data['E (MeV)'] > E_min) & (nld_data['E (MeV)'] < E_max+0.1)]

                    x,y,dy = nld_data_fit['E (MeV)'],nld_data_fit['NLD'],nld_data_fit['NLD uncertainity']

                    dy = np.where(dy == 0, 0.2*y, dy)
               
                    popt, pcov = curve_fit(lambda E, a, Delta: bsfg_fitting(E,a,Delta,A), xdata=x,ydata=y,sigma=dy,absolute_sigma=True)
                    

                    x_fit = np.linspace(E_min, E_max,100)

                    y_fit = bsfg_fitting(x_fit,*popt,A)

                    param_errors = np.sqrt(np.diag(pcov))

                    

                    fig.add_trace(go.Scatter(x=x_fit,y=y_fit,mode='lines',
                        name='a = {}, del = {}, <br> da = {}, ddel = {}'.format(np.round(popt[0],2),np.round(popt[1],2),np.round(param_errors[0],2),
                        np.round(param_errors[1],2))))

                    

                elif value_fit == 'All':

                    nld_data_fit = nld_data[(nld_data['E (MeV)'] > E_min) & (nld_data['E (MeV)'] < E_max+0.1)]

                    x,y,dy = nld_data_fit['E (MeV)'],nld_data_fit['NLD'],nld_data_fit['NLD uncertainity']

                    dy = np.where(dy == 0, 0.2*y, dy)
               
                    popt_bsfg, pcov_bsfg = curve_fit(lambda E, a, Delta: bsfg_fitting(E,a,Delta,A), xdata=x,ydata=y,sigma=dy,absolute_sigma=True)

                    x_fit = np.linspace(E_min, E_max,100)

                    y_fit_bsfg = bsfg_fitting(x_fit, *popt_bsfg,A)

                    param_errors_bsfg = np.sqrt(np.diag(pcov_bsfg))

                    

                    fig.add_trace(go.Scatter(x=x_fit,y=y_fit_bsfg,mode='lines',
                        name='a = {}, del = {}, <br> da = {}, ddel = {}'.format(np.round(popt_bsfg[0],2),np.round(popt_bsfg[1],2),
                        np.round(param_errors_bsfg[0],2),np.round(param_errors_bsfg[1],2))))

                    
                    popt_ctm, pcov_ctm = curve_fit(ctm_fitting, xdata=x,ydata=y,sigma=dy,absolute_sigma=True)

                    x_fit = np.linspace(E_min, E_max,100)

                    y_fit_ctm = ctm_fitting(x_fit, *popt_ctm)

                    param_errors_ctm = np.sqrt(np.diag(pcov_ctm))

                    

                    fig.add_trace(go.Scatter(x=x_fit,y=y_fit_ctm,mode='lines',
                        name='T = {}, E = {}, <br> dT = {}, dE = {}'.format(np.round(popt_ctm[0],2),np.round(popt_ctm[1],2),
                        np.round(param_errors_ctm[0],2),np.round(param_errors_ctm[1],2))))

                    

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
                    name=f"{data_df['Author'][i]} - {data_df['Isotope'][i]}"))

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

                

                fig.add_trace(go.Scatter(x=x_fit,y=y_fit,mode='lines',
                    name='T = {}, E = {}, <br> dT = {}, dE = {}'.format(np.round(popt[0],2),np.round(popt[1],2),np.round(param_errors[0],2),
                        np.round(param_errors[1],2))))

                
            elif value_fit == 'BSFG':

                nld_data_fit = nld_data[(nld_data['E (MeV)'] > E_min) & (nld_data['E (MeV)'] < E_max+0.1)]

                x,y,dy = nld_data_fit['E (MeV)'],nld_data_fit['NLD'],nld_data_fit['NLD uncertainity']
                
                dy = np.where(dy == 0, 0.2*y, dy)
                
                popt, pcov = curve_fit(lambda E, a, Delta: bsfg_fitting(E,a,Delta,A), xdata=x,ydata=y,sigma=dy,absolute_sigma=True)

                x_fit = np.linspace(E_min, E_max,100)

                y_fit = bsfg_fitting(x_fit, *popt,A)

                param_errors = np.sqrt(np.diag(pcov))

                

                fig.add_trace(go.Scatter(x=x_fit,y=y_fit,mode='lines',
                    name='a = {}, del = {}, <br> da = {}, ddel = {}'.format(np.round(popt[0],2),np.round(popt[1],2),np.round(param_errors[0],2),
                        np.round(param_errors[1],2))))

                
            elif value_fit == 'All':

                nld_data_fit = nld_data[(nld_data['E (MeV)'] > E_min) & (nld_data['E (MeV)'] < E_max+0.1)]

                x,y,dy = nld_data_fit['E (MeV)'],nld_data_fit['NLD'],nld_data_fit['NLD uncertainity']

                dy = np.where(dy == 0, 0.2*y, dy)
                
                popt_bsfg, pcov_bsfg = curve_fit(lambda E, a, Delta: bsfg_fitting(E,a,Delta,A), xdata=x,ydata=y,sigma=dy,absolute_sigma=True)

                x_fit = np.linspace(E_min, E_max,100)

                y_fit_bsfg = bsfg_fitting(x_fit, *popt_bsfg,A)

                param_errors_bsfg = np.sqrt(np.diag(pcov_bsfg))

                
                fig.add_trace(go.Scatter(x=x_fit,y=y_fit_bsfg,mode='lines',
                    name='a = {}, del = {}, <br> da = {}, ddel = {}'.format(np.round(popt_bsfg[0],2),np.round(popt_bsfg[1],2),
                        np.round(param_errors_bsfg[0],2),np.round(param_errors_bsfg[1],2))))


                popt_ctm, pcov_ctm = curve_fit(ctm_fitting, xdata=x,ydata=y,sigma=dy,absolute_sigma=True)

                x_fit = np.linspace(E_min, E_max,100)

                y_fit_ctm = ctm_fitting(x_fit, *popt_ctm)

                param_errors_ctm = np.sqrt(np.diag(pcov_ctm))

                
                fig.add_trace(go.Scatter(x=x_fit,y=y_fit_ctm,mode='lines',
                    name='T = {}, E = {},<br> dT = {}, dE = {}'.format(np.round(popt_ctm[0],2),np.round(popt_ctm[1],2),
                        np.round(param_errors_ctm[0],2),np.round(param_errors_ctm[1],2))))

                
            split_plots.append(dcc.Graph(id=f'graph-{i}',figure=fig))
          
    return [dcc.Graph(id='graph',figure=fig,style={"width":"100%","height":"60vh"})]




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
