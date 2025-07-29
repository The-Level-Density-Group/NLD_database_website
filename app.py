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
from dash import Dash, html
import dash_bootstrap_components as dbc 

app = Dash(__name__, use_pages=True,external_stylesheets=[dbc.themes.BOOTSTRAP],
     meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],)

app.config.suppress_callback_exceptions=True
app.title = "Level Densities"
server = app.server

# app.layout = html.Div([
    
    
#     # html.Div([
#     #     html.Div(
#     #         dcc.Link(f"{page['name']}", href=page["relative_path"],className='nav_bar'),
#     #     ) for page in dash.page_registry.values()
#     # ]),

#     # html.Div([html.Nav(className = "nav_bar", children=[
#     # 	html.A('Home', className="home_btn", href='/'),
#     #     html.A('Go to Database', className="search_by_Z_A_btn", href='/search-z-a'),
#     #     #html.A('Search by method', className="search_by_method_btn", href='/search-method'),
#     #     #html.A('Search by reaction', className="search_by_reaction_btn", href='#'),
#     #     #html.A('Search by status', className="search_by_status_btn", href='#'), 
#     # ])]),



#     dash.page_container
# ])


if __name__ == '__main__':
    app.run(debug=True)