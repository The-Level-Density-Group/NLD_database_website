from dash import Dash, html, dcc, callback, Input, Output, dash_table,dcc,State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd 
import numpy as np
import os

app = Dash(__name__)

app.layout = html.Div([
    html.H1(children='The Level Density Project',style={'textAlign':'center'}),
    html.H6(children='Enter mass number'),
    html.Div([
        "A: ",
        dcc.Input(id='mass-number', type='number')
    ]),
    html.H6(children='Enter proton number'),
    html.Div([
        "Z: ",
        dcc.Input(id='proton-number', type='number')
    ]),
    html.H6(children='Enter ID'),
    html.Div([
        "ID: ",
        dcc.Input(id='index', type='number')
    ]),
    html.Br(),
    html.Div([
    dash_table.DataTable(data=[],
        id = 'data_log_table'        
    )]),
    html.Div([
    dash_table.DataTable(data=[],
        id = 'selected_data'        
    )]),
    html.Br(),
    html.Div([
    dash_table.DataTable(data=[],
        id = 'datatable'        
    )]),
    html.Hr(),
    dcc.RadioItems(options=['linear','log'],value=1,id='controls-and-radio-item'),
    dcc.Graph(figure={},id='controls-and-graph')

])

@callback(
    Output(component_id='data_log_table', component_property='data'),
    [Input(component_id='mass-number', component_property='value'),
    Input(component_id='proton-number', component_property='value')]
)

def update_log(A,Z):
    nld_log_file = pd.read_csv('Arranged_data.csv',header=0,sep=',')
    # Drop the rows where the datafile doesn't exist
    nld_log_file.dropna(subset=['Datafile'],inplace = True)
    nld_log_file = nld_log_file.reset_index()
    nld_log_file[['B','C','D','E','file']] = nld_log_file['Datafile'].str.split("\\",expand=True)
    #nld_log_file['file'] = nld_log_file['file'].str.replace('.dat','.csv')
    # drop the datafile column because I will display the data on the website itself.
    nld_log_file.drop('Datafile',inplace=True,axis=1)
    nld_log_file['Validation'] = nld_log_file['Validation'].replace(np.nan,'yes')
   
    log_data = nld_log_file[(nld_log_file['Z'] == Z) & (nld_log_file['A'] == A)]
    return log_data.to_dict('records')

@callback(
    [Output(component_id='datatable',component_property='data'),
    Output(component_id='selected_data',component_property='data')],
    [Input(component_id='data_log_table',component_property='selected_rows'),
     Input(component_id='index',component_property='value')],
    [State(component_id='mass-number', component_property='value'),
     State(component_id='proton-number', component_property='value')]
)

def selected_log_book(selected_rows,i,A,Z):
    log_data = update_log(A,Z)
    log_data_df = pd.DataFrame(log_data,columns=['ID','Nucleus','Z','A','Emin','Emax','Reaction','Method','Reference','Author','Validation','NR_flag','Comments','B','C','D','E','file'])
    log_data_selected = log_data_df[log_data_df['ID'] == i]

    nld_folder = str(Z) + '_' + str(A) # data folder is formatted as Z_A

    
    filename = log_data_selected['file'].iloc[0] 
    file_path = os.path.join(nld_folder, filename)
            # the first 2 or 3 lines in each csv file is just comments (to be ignored) starting with hashtag
    nld_file = pd.read_csv(file_path, comment='#', header=None)
            # the dataframe also includes an extra column. So I am dropping it.
    nld_file.drop(3, axis=1, inplace=True)
            # renaming columns
    nld_file.rename(columns={0: "E (MeV)", 1: "NLD", 2: "NLD uncertainity"}, inplace=True)
    
    return nld_file.to_dict('records'), log_data_selected.to_dict('records')                                                                                                                                                                                                                    
'''
@callback(
    Output(component_id='datatable',component_property='data'),
    [Input(component_id='selected_data',component_property='selected_rows')],
    [State(component_id='index', component_property='value'),
     State(component_id='mass-number', component_property='value'),
     State(component_id='proton-number', component_property='value')]
    
)

def update_output(selected_rows,i,A,Z):
    nld_log_file = selected_log_book(selected_rows,i,A,Z)
    print(nld_log_file)
    nld_log_file_df = pd.DataFrame(nld_log_file,columns=['ID','Nucleus','Z','A','Emin','Emax','Reaction','Method','Reference','Author','Validation','NR_flag','Comments','B','C','D','E','file'])
    nld_folder = str(Z) + '_' + str(A) # data folder is formatted as Z_A

    
    filename = nld_log_file_df['file'].astype(str)
    print(filename)   
    file_path = os.path.join(nld_folder, filename)
            # the first 2 or 3 lines in each csv file is just comments (to be ignored) starting with hashtag
    nld_file = pd.read_csv(file_path, comment='#', header=None)
            # the dataframe also includes an extra column. So I am dropping it.
    nld_file.drop(3, axis=1, inplace=True)
            # renaming columns
    nld_file.rename(columns={0: "E (MeV)", 1: "NLD", 2: "NLD uncertainity"}, inplace=True)
    
    return nld_file.to_dict('records')

'''
@callback(
    Output(component_id='controls-and-graph',component_property='figure'),
    [Input(component_id='datatable',component_property='selected_rows'),
    Input(component_id='controls-and-radio-item', component_property='value')],
    [State(component_id='index', component_property='value'),
    State(component_id='mass-number', component_property='value'),
    State(component_id='proton-number', component_property='value')]
)

def log_plot(selected_rows,scale,i,A,Z):
    df = selected_log_book(selected_rows,i,A,Z)[0]
    fig = go.Figure()
    if scale == 'linear':
        fig = px.scatter(df,x='E (MeV)',y='NLD',log_y=False,error_y='NLD uncertainity')
    elif scale == 'log':
        fig = px.scatter(df,x='E (MeV)',y='NLD',log_y=True,error_y='NLD uncertainity')

    return fig

if __name__ == '__main__':
    app.run(debug=True)