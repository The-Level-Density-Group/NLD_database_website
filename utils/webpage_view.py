from dash import dcc,dash_table
from dash import html
import os
import pandas as pd
import plotly.graph_objects as go
import dash_bootstrap_components as dbc


df_NLD = pd.read_excel('log_book_new.xlsx')

unique_reactions = set()
for reactions in df_NLD['Reaction']:
   if isinstance(reactions,str):
       for reaction in reactions.split(';'):
           unique_reactions.add(reaction.strip())


# Flagging results from ctbsfgcomposite pipeline
FLAG_CSV = 'flag_results.csv'
SKIPPED_CSV = 'skipped_files.csv'
COLOR_RECOMMENDED = '#2E8B57'      
COLOR_NOT_RECOMMENDED = '#B5E3B5'  
COLOR_UNASSESSABLE = '#888888'     

if os.path.isfile(FLAG_CSV):
    df_flags = pd.read_csv(FLAG_CSV)
else:
    df_flags = pd.DataFrame(columns=['Z', 'A', 'file', 'any_flagged',
                                     'ct_flagged', 'bsfg_flagged',
                                     'chi_ct_flag', 'chi_b_flag',
                                     'mb_ct_flag', 'mb_b_flag',
                                     'p_ct', 'p_b', 'ct_ok', 'bsfg_ok'])

if os.path.isfile(SKIPPED_CSV):
    df_skipped = pd.read_csv(SKIPPED_CSV)
else:
    df_skipped = pd.DataFrame(columns=['file', 'reason', 'Z', 'A'])


def _fmt_p(p):
    return f"{p:.2g}" if pd.notna(p) else "N/A"


def _flag_detail(row):
    """Build a human-readable per-model flag string for a Not-Recommended row."""
    bits = []
    if row['ct_flagged']:
        sub = []
        if row['chi_ct_flag']:
            sub.append(f"chi (p={_fmt_p(row['p_ct'])})")
        elif pd.isna(row['p_ct']):
            sub.append("chi N/A")
        if row['mb_ct_flag']:
            sub.append("mb")
        bits.append("CT: " + ", ".join(sub))
    if row['bsfg_flagged']:
        sub = []
        if row['chi_b_flag']:
            sub.append(f"chi (p={_fmt_p(row['p_b'])})")
        elif pd.isna(row['p_b']):
            sub.append("chi N/A")
        if row['mb_b_flag']:
            sub.append("mb")
        bits.append("BSFG: " + ", ".join(sub))
    return " | ".join(bits)


def _unassessable_reason_from_flags(row):
    bits = []
    if not row['ct_ok']:
        bits.append("CT fit unavailable")
    if not row['bsfg_ok']:
        bits.append("BSFG fit unavailable")
    return "; ".join(bits) if bits else "no valid p-value"


# compute the three buckets
_both_p_nan = df_flags['p_ct'].isna() & df_flags['p_b'].isna() if len(df_flags) else pd.Series([], dtype=bool)
recommended_df = df_flags[(~df_flags['any_flagged']) & (~_both_p_nan)].copy() if len(df_flags) else df_flags.copy()
not_recommended_df = df_flags[df_flags['any_flagged']].copy() if len(df_flags) else df_flags.copy()
_unassessable_from_flags = df_flags[(~df_flags['any_flagged']) & _both_p_nan].copy() if len(df_flags) else df_flags.copy()

if len(not_recommended_df):
    not_recommended_df['detail'] = not_recommended_df.apply(_flag_detail, axis=1)
else:
    not_recommended_df['detail'] = []

if len(_unassessable_from_flags):
    _unassessable_from_flags['reason'] = _unassessable_from_flags.apply(_unassessable_reason_from_flags, axis=1)
else:
    _unassessable_from_flags['reason'] = []

unassessable_df = pd.concat([
    df_skipped[['file', 'Z', 'A', 'reason']],
    _unassessable_from_flags[['file', 'Z', 'A', 'reason']],
], ignore_index=True)

n_recommended = int(len(recommended_df))
n_not_recommended = int(len(not_recommended_df))
n_unassessable = int(len(unassessable_df))


def make_flag_donut(n_rec, n_not, n_un):
    #Donut with the three buckets
    total = int(n_rec) + int(n_not) + int(n_un)
    if total == 0:
        values = [1, 0, 0]
        center_top = "0"
    else:
        values = [int(n_rec), int(n_not), int(n_un)]
        center_top = str(int(n_not))

    fig = go.Figure(data=[go.Pie(
        labels=['Recommended', 'Not Recommended', 'Unassessable'],
        values=values,
        hole=0.65,
        marker=dict(colors=[COLOR_RECOMMENDED, COLOR_NOT_RECOMMENDED, COLOR_UNASSESSABLE],
                    line=dict(color='rgb(30,30,30)', width=2)),
        sort=False,
        direction='clockwise',
        textinfo='none',
        hovertemplate='%{label}: %{value} (%{percent})<extra></extra>',
    )])

    fig.update_layout(
        paper_bgcolor='rgb(30,30,30)',
        plot_bgcolor='rgb(30,30,30)',
        font=dict(color='orange', size=12),
        showlegend=True,
        legend=dict(orientation='h', y=-0.10, x=0.5, xanchor='center',
                    font=dict(color='orange', size=10)),
        margin=dict(l=10, r=10, t=10, b=10),
        height=270,
        annotations=[
            dict(text=f"<b style='font-size:22px'>{center_top}</b>"
                      f"<br><span style='font-size:11px'>not rec. of {total}</span>",
                 x=0.5, y=0.5, showarrow=False,
                 font=dict(color='orange')),
        ],
    )
    return fig


def _file_row(file_name, z, a, extra=None):
    label = f"{file_name}  (Z={int(z)}, A={int(a)})"
    if extra:
        label += f"  —  {extra}"
    return html.Div(label, className='classified-row')


def build_recommended_children():
    rows = [_file_row(r['file'], r['Z'], r['A']) for _, r in recommended_df.iterrows()]
    return rows or [html.Div("No files in this bucket.", className='classified-empty')]


def build_unassessable_children():
    rows = [_file_row(r['file'], r['Z'], r['A'], extra=r['reason'])
            for _, r in unassessable_df.iterrows()]
    return rows or [html.Div("No files in this bucket.", className='classified-empty')]


def build_not_recommended_children(scope='all'):
    #scope: 'all' | 'ct' | 'bsfg' | 'both'
    if scope == 'ct':
        sub = not_recommended_df[not_recommended_df['ct_flagged'] & ~not_recommended_df['bsfg_flagged']]
    elif scope == 'bsfg':
        sub = not_recommended_df[not_recommended_df['bsfg_flagged'] & ~not_recommended_df['ct_flagged']]
    elif scope == 'both':
        sub = not_recommended_df[not_recommended_df['ct_flagged'] & not_recommended_df['bsfg_flagged']]
    else:
        sub = not_recommended_df
    rows = [_file_row(r['file'], r['Z'], r['A'], extra=r['detail']) for _, r in sub.iterrows()]
    return rows or [html.Div("No files match this filter.", className='classified-empty')]


def build_classified_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Classified Datasets")),
            dbc.ModalBody([
                dbc.Tabs(id='classified-tabs', active_tab='tab-rec', children=[
                    dbc.Tab(
                        label=f"Recommended ({n_recommended})",
                        tab_id='tab-rec',
                        children=html.Div(build_recommended_children(),
                                          className='classified-list'),
                    ),
                    dbc.Tab(
                        label=f"Not Recommended ({n_not_recommended})",
                        tab_id='tab-notrec',
                        children=html.Div([
                            html.Div(
                                dbc.RadioItems(
                                    id='nr-scope',
                                    options=[
                                        {'label': 'All', 'value': 'all'},
                                        {'label': 'CT only', 'value': 'ct'},
                                        {'label': 'BSFG only', 'value': 'bsfg'},
                                        {'label': 'Both models', 'value': 'both'},
                                    ],
                                    value='all',
                                    inline=True,
                                ),
                                className='nr-scope-row',
                            ),
                            html.Div(build_not_recommended_children('all'),
                                     id='nr-list', className='classified-list'),
                        ]),
                    ),
                    dbc.Tab(
                        label=f"Unassessable ({n_unassessable})",
                        tab_id='tab-un',
                        children=html.Div(build_unassessable_children(),
                                          className='classified-list'),
                    ),
                ]),
            ]),
            dbc.ModalFooter(dbc.Button("Close", id="close-classified-modal", n_clicks=0)),
        ],
        id="classified-modal",
        size="xl",
        is_open=False,
        scrollable=True,
    )

def view():
    return \
    html.Div(id="body", className="container scalable", children=[
        html.A(html.H1('Current Archive of Nuclear Density of Levels',className='website_header_database'),href='/',className='header_banner_link_database'),
        html.P([
            'If this website was helpful to your research, please consider ',
            html.A('citing our article', href='https://www.sciencedirect.com/science/article/pii/S0010465525005193',
                   style={'color': 'white', 'textDecoration': 'underline'}),
            '.'
        ], style={'color': 'white', 'fontStyle': 'italic', 'textAlign': 'center', 'marginTop': '8px', 'marginBottom': '4px'}),
        html.Hr(id='banner_hr'),
        html.Div(id="app-container", children=[
            html.Div(id="left-column", children=[
                html.P('Search Criteria:',id='search_criteria_header'),
                dcc.Dropdown(df_NLD['Z'].sort_values().unique(), id='proton-number', value=None, className="input1", placeholder='Enter Proton Number'),
                dcc.Dropdown(id='mass-number', value=None, className="input2", placeholder='Enter Mass Number'),

                html.Hr(id='criteria_hr'),

                html.P('Filter by method:',id='method_filter_header'),
                html.Div(dbc.Checklist(options=[{"label": "Evaporation", "value": 'Evaporation'},{"label": "Oslo", "value":'Oslo'},
                    {"label": "Ericson", "value":'Ericson'},{"label": "Inverse Oslo", "value":'Inverse Oslo'},{"label": "Beta Oslo", "value":'Beta Oslo'}
                    ,{"label": "Beta-n", "value":'Beta-n'},{"label": "Beta-p", "value":'Beta-p'}
                    ],
                    id="method_btn",inline=True,switch=True),className='method-btn'),

               dcc.Dropdown(id='search_by_reaction',options=[{'label': reaction, 'value': reaction} for reaction in unique_reactions],
                   placeholder="Select or type a reaction",searchable=True,clearable=True,),

               html.Div(html.A(html.Button('Clear All Filters', id='clear_filter_btn',className='clear-btn'),href='/search-z-a'),className='clear-btn-container'),

                #html.Div(dbc.Input(id='search_by_reaction',type='text',placeholder='Search by Reaction. E.g.: d,p or 7Li,p')),

                html.Div(dbc.Checklist(options=[{"label": "Recommended", "value": 'Accepted'},{"label": "Not Recommended", "value":'Rejected'},
                    {'label':'Under Review','value':'Probation'}],id="status_btn",inline=True,switch=True),className='status-btn'),

                html.Div([
                    html.P('Automated Assessment:', className='donut-header'),
                    dcc.Graph(
                        id='flag-donut',
                        figure=make_flag_donut(n_recommended, n_not_recommended, n_unassessable),
                        config={'displayModeBar': False},
                    ),
                    html.Button('View classified datasets',
                                id='open-classified-modal',
                                className='view-classified-btn',
                                n_clicks=0),
                ], className='donut-container'),

                build_classified_modal(),

                html.Div([html.Button('Download CSV', id='download_btn', className="button1"),
                    dcc.Download(id="download-data")],className='download-btn-class'),

                
                html.Div(html.Button('Split/Unsplit plots', id='split_unsplit_btn', className="button2",n_clicks=0)),

                
            ]),


            html.Div(id='center-column', children=[html.Div(dbc.Checklist(options=[{"label": "Select all", "value": 'select all'}],
            id="select_btn",inline=True),className='select-btn'),

            html.Div([dash_table.DataTable(data=[],id='data_log_table',
                tooltip_header={
                'Emin': 'Minimum energy value used for the fitting',
                'Emax': 'Maximum energy value used for the fitting',
                'Exrange': 'Emax - Emin',
                'Method': 'Method by which level densities were extracted',
                'Reaction':'Primary reaction used for level density extraction',
                'Deformation':'Deformation of the nucleus (extracted from NNDC)'
                },
                row_selectable='multi',
                style_table={'width': '100%','overflowX':'auto'},
                style_header={'backgroundColor': 'rgb(30,30,30)','color': 'orange','border':'2px solid white'},
                style_data={'backgroundColor': 'rgb(50,50,50)','color': 'orange','border':'2px solid white'},
                style_cell_conditional=[
                    {'if': {'column_id': 'Reference'}, 'maxWidth': '300px', 'whiteSpace': 'normal', 'overflow': 'hidden', 'textOverflow': 'ellipsis'},
                ],
                page_size=10,
                )]),

                html.Div(dbc.Checklist(options=[{"label": "Reset all", "value": 'deselect all'}],
            id="deselect_btn",inline=True),className='deselect-btn'),

                html.Div([dash_table.DataTable(data=[],id='selected_data',row_selectable='multi', 
                    style_table={'width': '100%','borderRadius': '5px','overflowX':'auto'},
                    style_header={'backgroundColor': 'rgb(30,30,30)','color': 'orange','border':'2px solid orange'},
                    style_data={'backgroundColor': 'rgb(50,50,50)','color': 'orange','border':'2px solid orange'},)],className='datatable'),

                
                

                html.Div(dbc.RadioItems(options=[{"label": "Log", "value": 'log'},{"label": "Linear", "value":'linear'},],
            value='linear',id="radio_btn",inline=True,switch=True),className='scaling-btn'),

                html.Div(dbc.RadioItems(options=[{'label':'CT Model','value':'CTM'},{'label':'BSFG Model','value':'BSFG'},
                    {'label':'All Models','value':'All'},{'label':'Reset','value':'Reset'}],
        id='radio_btn_fitting',inline=True),className='radio-btn-fitting-container'),

                dcc.Loading(children=[
                    html.Div(id="div-graphs")
                ])
            ]),                   
        ]),
    ]),


