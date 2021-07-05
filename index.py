#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, ‎July ‎4, ‎2021, ‏‎19:39
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""


import dash_core_components as dcc
import dash_html_components as html
import dash_table as table
import mysql.connector
import pandas as pd
from dash.dependencies import Input, Output, State

import otros.keys as keys
from app import app
# from apps import app1


app.layout = html.Div(className='mainContainer', children=[
    html.Link(rel="stylesheet",
        href="https://fonts.googleapis.com/css?family=Montserrat"),
    html.Div(className='column', children=[
        html.H1('Formulario'),
        html.Hr()
    ]),
    html.Div(className='pretty-container', children=[
        html.Div(className='one-third column', children=[
            html.Div(className='row', children=[
                html.Span('No.'),
                dcc.Input(),
            ]),
            html.Div(className='row', children=[
                html.Span('Apellidos'),
                html.Div(className='auto-column', children=[
                    dcc.Input(),
                    dcc.Input(),
                ])
            ]),
            html.Div(className='row', children=[
                html.Span('Nombre'),
                dcc.Input(),
            ]),
            html.Div(className='row', children=[
                html.Span('Cédula'),
                dcc.Input(),
            ]),
            html.Div(className='row', children=[
                html.Span('Fecha de nacimiento'),
                dcc.Input(),
            ]),
            html.P('', className='spacer'),
            dcc.RadioItems(className='radio-items', id='search-type',
                options=[
                    {'value':'ambigua', 'label':'Ambigua'},
                    {'value':'precisa', 'label':'Precisa'},
                    {'value':'exacta', 'label':'Exacta'},
                ], value='precisa'
            ),
            html.Button('BUSCAR', className='large-button'),
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
            )
        ])
    ]),
])


# @app.callback(
#     Output('page-content', 'children'),
#     Input('url', 'pathname')
# )
# def display_page(pathname):
#     if pathname == '/apps/app1':
#         return app1.layout
#     else:
#         return '404'


if __name__ == '__main__':
    app.run_server(debug=True)