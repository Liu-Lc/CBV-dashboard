#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, ‎July ‎4, ‎2021, ‏‎19:42
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""


import dash_core_components as dcc
import dash_html_components as html
import dash_table as table
from dash.dependencies import Input, Output

from app import app


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
                    dcc.Tab(
                        label='Verificar', value='verificar',
                        className='tab', selected_className='tab-selected',
                    ),
                ]
            ),
            html.Div(className='tabs-unique-container', children=[
                table.DataTable(
                    columns=[
                        {'id':'apellido', 'name':'Apellido'},
                        {'id':'nombre', 'name':'Nombre'},
                        {'id':'cedula', 'name':'Cédula'},
                        {'id':'fecha_nac', 'name':'Fecha de nacimiento'},
                        {'id':'number', 'name':'No.'},
                    ],
                    fixed_rows={'headers': True},
                    style_table={'height': 400},
                ),
                html.Div(className='button-container', children=[
                    html.Button('ACTUALIZAR', id='button-actualizar', className='large-button'),
                    html.Button('LIMPIAR', id='button-modificar', className='large-button'),
                    html.Button('MODIFICAR', id='button-eliminar', className='large-button'),
                ]),
            ]),
        ])


# @app.callback(
#     Output('app-1-display-value', 'children'),
#     Input('app-1-dropdown', 'value'))
# def display_value(value):
#     return 'You have selected "{}"'.format(value)