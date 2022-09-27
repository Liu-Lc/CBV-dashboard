#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, July 4, 2021, 19:39
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""


from dash import dcc, html, callback_context as ctx
from dash.dependencies import Input, Output, State
from app import app, auth
from apps import form, ver
import mysql.connector
from otros import keys


header = html.Div([
            html.Link(rel="stylesheet",
                href="https://fonts.googleapis.com/css?family=Montserrat"),
            html.Link(rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.0/css/all.min.css"),
            html.Div(className='column', children=[
                html.H1('Formulario'),
                html.Hr(),
                html.Div(className='row right', children=[
                    dcc.Loading(id='loading-connection', type='circle', children=[
                        html.I(className='fa fa-square-check fa-green', id='connection-good', style={'display':'none'}),
                        html.I(className='fa fa-square-xmark fa-red', id='connection-bad', style={'display':'none'}),
                    ], className='size-small'),
                    html.Spacer(),
                    html.Span('Conexión', className='right'),
                ]),
            ]),
            html.Spacer(),
        ])

app.layout = html.Div(className='mainContainer', children=[
    header,
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
            html.I(className='fa fa-cogs')
        ]),
    ]),
    html.Div(id='content-page', children=[]),
])


@app.callback(
    [Output('connection-good', 'style'), Output('connection-bad', 'style')],
    [Input('tabs-main', 'value')],
    [State('connection-good', 'style'), State('connection-bad', 'style')] 
)
def connection_check(tab, good, bad):
    try:
        conn = mysql.connector.connect(**keys.config)
        connection = conn.is_connected()
        conn.close()
        if connection: return [{}, bad]
        else: return [good, {}]
    except: return [good, {}]

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