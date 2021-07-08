#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, ‎July ‎4, ‎2021, ‏‎19:42
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""


import dash_core_components as dcc
import dash_html_components as html
import dash_table as table
import mysql.connector
import pandas as pd
from app import app
from dash.dependencies import Input, Output
from otros import keys


layout = html.Div(className='column', children=[
            dcc.Tabs(
                id="tabs-ver",
                value='todos',
                parent_className='tabs-container-no-shadow',
                className='tabs',
                children=[
                    dcc.Tab(
                        label='Ver Todos', value='todos',
                        className='tab', selected_className='tab-selected',
                    ),
                    dcc.Tab(
                        label='Vacios', value='vacios',
                        className='tab', selected_className='tab-selected',
                    ),
                    dcc.Tab(
                        label='Duplicados', value='duplicados',
                        className='tab', selected_className='tab-selected',
                    ),
                    # dcc.Tab(
                    #     label='Verificar', value='verificar',
                    #     className='tab', selected_className='tab-selected',
                    # ),
                ]
            ),
            html.Div(className='tabs-unique-container', children=[
                dcc.Dropdown(id='ver-option', className='dropdown-style', 
                    clearable=False, searchable=False),
                dcc.Loading(
                    id='loading-table', type='default', children=[
                table.DataTable(id='table-ver',
                    columns=[
                        {'id':'id', 'name':'id'},
                        {'id':'apellido', 'name':'Apellido'},
                        {'id':'nombre', 'name':'Nombre'},
                        {'id':'cedula', 'name':'Cédula'},
                        {'id':'fechanac', 'name':'F. Nac.'},
                        {'id':'number', 'name':'No.'},
                    ],
                    fixed_rows={'headers': True},
                            # page_action='none',
                            page_size=200,
                    style_table={'height': '400px', 'overflowY': 'auto'},
                    # style_header={'textAlign': 'center'},
                    style_cell_conditional=[
                        {'if': {'column_id': c},
                            'width': '8%'} for c in ['id', 'number']
                    ] + [
                        {'if': {'column_id': 'cedula'},
                            'width': '15%'},
                        {'if': {'column_id': 'fechanac'},
                            'width': '12%'} ,
                    ],
                    style_cell={'textAlign': 'center', 'min-width': '50px'},
                ),
                    ]
                ),
                html.Div(className='button-container', children=[
                    html.Button('ACTUALIZAR', id='button-actualizar', className='large-button'),
                    html.Button('MODIFICAR', id='button-modificar', className='large-button'),
                    html.Button('ELIMINAR', id='button-eliminar', className='large-button'),
                ]),
            ]),
        ])


@app.callback(
    Output('table-ver', 'data'),
    Input('tabs-ver', 'value')
)
def display_value(value):
    if value=='todos':
        conn = mysql.connector.connect(**keys.config)
        query = '''select * from clinica order by NO desc limit 100; '''
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return pd.DataFrame(results, 
            columns=['id', 'apellido', 'nombre', 
                'cedula', 'fecha_nac', 'number']).to_dict('records')
    else: return []
