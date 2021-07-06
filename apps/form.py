#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, ‎July ‎6, ‎2021, ‏‎08:32
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""


import dash_core_components as dcc
import dash_html_components as html
import dash_table as table
import pandas as pd
from app import app
from dash.dependencies import Input, Output, State


header = html.Div([html.Link(rel="stylesheet",
        href="https://fonts.googleapis.com/css?family=Montserrat"),
    html.Div(className='column', children=[
        html.H1('Formulario'),
        html.Hr()
    ]),
])

form =  html.Div(className='container', children=[
            html.Div(className='one-third column', children=[
                html.Div(className='row', children=[
                    html.Span('Apellidos', className='label'),
                    html.Div(className='auto-column', children=[
                        dcc.Input(),
                        dcc.Input(),
                    ])
                ]),
                html.Div(className='row', children=[
                    html.Span('Nombre', className='label'),
                    dcc.Input(),
                ]),
                html.Div(className='row', children=[
                    html.Span('Cédula', className='label'),
                    dcc.Input(),
                ]),
                html.Div(className='row', children=[
                    html.Span('Fecha de nacimiento', className='label'),
                    dcc.DatePickerSingle(className='input-style'),
                ]),
                html.P('', className='spacer'),
                dcc.RadioItems(className='radio-items', id='search-type',
                    options=[
                        {'value':'ambigua', 'label':'Ambigua'},
                        {'value':'precisa', 'label':'Precisa'},
                        {'value':'exacta', 'label':'Exacta'},
                    ], value='precisa'
                ),
                html.Button('BUSCAR', id='button-buscar', className='large-button'),
            ]),
            html.Div(className='two-thirds column table', children=[
                table.DataTable(id='table-buscar',
                    columns=[
                        {'id':'apellido', 'name':'Apellido'},
                        {'id':'nombre', 'name':'Nombre'},
                        {'id':'cedula', 'name':'Cédula'},
                        {'id':'fecha_nac', 'name':'Fecha de nacimiento'},
                        {'id':'number', 'name':'No.'},
                    ]
                ),
                html.Div(className='row', children=[
                    html.Button('LIMPIAR', id='button-limpiar1', className='large-button'),
                    html.Button('MODIFICAR', id='button-modificar1', className='large-button'),
                    html.Button('ELIMINAR', id='button-eliminar1', className='large-button'),
                ]),
            ]),
        ])

form_add =  html.Div(className='container', children=[
                html.Div(className='one-third column', children=[
                    html.Div(className='row', children=[
                        html.Span('No.', className='label'),
                        dcc.Input(),
                    ]),
                    html.Div(className='row', children=[
                        html.Span('Apellidos', className='label'),
                        dcc.Input(),
                    ]),
                    html.Div(className='row', children=[
                        html.Span('Nombre', className='label'),
                        dcc.Input(),
                    ]),
                    html.Div(className='row', children=[
                        html.Span('Cédula', className='label'),
                        dcc.Input(),
                    ]),
                    html.Div(className='row', children=[
                        html.Span('Fecha de nacimiento'),
                        dcc.DatePickerSingle(),
                    ]),
                    html.P('', className='spacer'),
                    html.Button('AGREGAR', id='button-agregar', className='large-button'),
                ]),
                html.Div(className='two-thirds column table', children=[
                    table.DataTable(
                        columns=[
                            {'id':'apellido', 'name':'Apellido'},
                            {'id':'nombre', 'name':'Nombre'},
                            {'id':'cedula', 'name':'Cédula'},
                            {'id':'fecha_nac', 'name':'Fecha de nacimiento'},
                            {'id':'number', 'name':'No.'},
                        ]
                    ),
                    html.Div(className='row', children=[
                        html.Button('LIMPIAR', id='button-limpiar2', className='large-button'),
                        html.Button('MODIFICAR', id='button-modificar2', className='large-button'),
                        html.Button('ELIMINAR', id='button-eliminar2', className='large-button'),
                    ]),
                ])
            ])


@app.callback(
    Output('table-buscar', 'data'),
    [Input('button-buscar', 'n_clicks')]
)
def button_buscar_click(nclick):
    return {}
