#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, July 4, 2021, 19:39
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""


import dash
from dash import dcc, html, callback_context as ctx
import mysql.connector
import pandas as pd
from dash.dependencies import Input, Output, State

import otros.keys as keys
from app import app
from apps import form, ver


app.layout = html.Div(className='mainContainer', children=[
    form.header,
    html.Div([
        html.Div(id='side-panel', className='side-panel', 
            children=[
                html.Button(id='close-button', className='close-button', children=[
                    html.I(className='fa fa-close')
                ]),
                dcc.Location(id='url'),
                html.Br(),
                dcc.Link('Formulario', href='/'),
                html.Br(),
                dcc.Link('Ver', href='/ver'),
                html.Br(),
                dcc.Link('Conexión', href='/conexion'),
                html.Br(),
                dcc.Link('Configuración avanzada', href='/config'),
            ], style={'width': '0px'},
        ),
        html.Button(id='config-button', className='config-button', children=[
            html.I(className='fa fa-cogs fa-xl')
        ]),
    ]),
    html.Div(id='content-page', children=[]),
])


@app.callback(
    Output('side-panel', 'style'),
    Input('config-button', 'n_clicks'),
    Input('close-button', 'n_clicks'),
    Input('url', 'pathname')
)
def config_button_click(open_click, close_click, path):
    button = ctx.triggered_id
    if button=='config-button':
        return {'width': '250px'}
    else: return {'width': '0px'}

@app.callback(
    Output('content-page', 'children'),
    Input('url', 'pathname')
)
def change_url(pathname):
    if pathname=='/ver':
        return ver.layout
    else: return form.tabs


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)