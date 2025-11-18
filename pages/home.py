'''
This file is part of The Level Density project website (www.nld.ascsn.net).

The Level Density project website is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The Level Density project website is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

'''

import dash
from dash import html, dcc, callback, Input, Output
import pandas as pd 

dash.register_page(__name__, path='/',title='Home',name='Home')

# Load the main file that has information about all data sets.
df_NLD = pd.read_excel('log_book_new.xlsx')

# layout of the homepage.
layout = html.Div([
	# We need a main heading.
	html.A(html.H1('Current Archive of Nuclear Density of Levels',className='website_header'),href='/',className='header_banner_link'),

	# Content of the page.
	html.H3('Welcome to the Level Density Project Database!',style={'textAlign':'center',}),

    html.P('The CANDL database is home to experimental level density data extracted via different techniques like evaporation method, Oslo method and its variants, Ericson fluctuations, \
     scattering wavelet technique etc. You can search for datasets using the proton number and mass number or filter the datasets by the methods or \
     search by the type of reaction or filter the datasets by their staus (Accepted, Rejected or Probation). You can also fit any selected datasets \
     to the constant temperature (CT) model and the back-shifted Fermi gas (BSFG) model. This database has been made possible by the contributions of Chirag Rathi, \
      Dr. Alexander Voinov, Kristen Leibensperger, Dr. Zach Meisel and Dr. Kyle Godbey.',className='intro_heading'),


    html.H4('Total Number of Available Datasets',className='dataset-counter-heading',id='dataset_heading'),

    # created a div to count the number of datasets and referenced the ID in counter.js file for some cool animation.
    html.Div(id='dataset_counter',className='counter'),
    #html.Span('0', id='dataset_counter', **{'data-target': '0'},className='counter'),

    # A clickable button that takes you to the database.
    html.Div(html.A(html.Button('Go to Database', id='go_to_database_btn',className='database-btn'),href='/search-z-a'),className='database-btn-container'),

    html.P(['If you would like to submit your dataset to this database or if you would like to inquire about an available dataset, please forward \
    	your queries to ',html.A('The Level Density Group', href='mailto:theleveldensitygroup@gmail.com',style={'color':'orange'})],
        className='contact-info-section'),


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

  target_number = len(df)

  return str(target_number)




