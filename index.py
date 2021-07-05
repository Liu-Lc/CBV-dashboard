#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, ‎July ‎4, ‎2021, ‏‎19:39
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""


import dash_core_components as dcc
import dash_html_components as html
import mysql.connector
import pandas as pd
from dash.dependencies import Input, Output, State

import otros.keys as keys
from app import app
from apps import app1


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/apps/app1':
        return app1.layout
    elif pathname == '/apps/app2':
        return app2.layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=True)