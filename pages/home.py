import dash
from dash import html, dcc, callback, Input, Output
import pandas as pd 

dash.register_page(__name__, path='/',title='Home',name='Home')

# Load the main file that has information about all data sets.
df_NLD = pd.read_excel('../OhioUniversity/PhD/NLDD/data_sets/log_book_new.xlsx')

# layout of the homepage.
layout = html.Div([
	# We need a main heading.
	html.A(html.H1('The Level Density Project',className='website_header'),href='/',className='header_banner_link'),

	# Content of the page.
	html.H3('Welcome to the Level Density Project Database!',style={'textAlign':'center',}),

    html.P('This database is home to experimental level density data extracted via different techniques like evaporation method, Oslo method and its variants, Ericson fluctuations, \
     scattering wavelet technique etc. You can search for datasets using the proton number and mass number or filter the datasets by the methods or \
     search by the type of reaction or filter the datasets by their staus (Accepted, Rejected or Probation). You can also fit any selected datasets \
     to the constant temperature (CT) model and the back-shifted Fermi gas (BSFG) model. This database has been made possible by the contributions of Chirag Rathi, \
      Dr. Alexander Voinov, Dr. Zach Meisel and Dr. Kyle Godbey.',className='intro_heading'),


    html.H4('Total Number of Available Datasets',className='dataset-counter-heading',id='dataset_heading'),

    # created a div to count the number of datasets and referenced the ID in counter.js file for some cool animation.
    html.Div(id='dataset_counter',className='counter'),

    # A clickable button that takes you to the database.
    html.A(html.Button('Go to Database', id='go_to_database_btn',className='database-btn'),href='/search-z-a'),

    html.P(['If you would like to submit your dataset to this database or if you would like to inquire about an available dataset, please forward \
    	your queries to ',html.A('Dr. Alexander Voinov', href='mailto:voinov@ohio.edu',style={'color':'orange'})],
        style={'textAlign':'center','font-size':'16px','margin-top':'12rem','font-weight':'bold'}),


    # To store the entire main log file (without displaying it on the webpage.)
    dcc.Store(id='full-data-store',data=df_NLD.to_dict('records'))
])

# callback function that takes in the main file and returns the number of available dataset.
@callback(Output('dataset_counter','children'),Input('full-data-store','data'))

def counter(data):

	'''Function to count the number of available datasets.
	Input: data - stores the entire main data log file.
	Output: Length of the main log file.'''

	df = pd.DataFrame(data)

	return str(len(df))