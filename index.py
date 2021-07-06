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
from apps import form


app.layout = html.Div(className='mainContainer', children=[
    form.header,
    dcc.Tabs(
        id="tabs-with-classes",
        value='tab-1',
        parent_className='custom-tabs',
        className='custom-tabs-container',
        children=[
            dcc.Tab(
                label='Formulario',
                value='tab-1',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=[form.form]
            ),
            dcc.Tab(
                label='Agregar',
                value='tab-2',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=[form.form_add]
            ),
        ]),
])


# @app.callback(
#     Output(''),
#     [Input('button-agregar', 'n_clicks')]
# )


if __name__ == '__main__':
    app.run_server(debug=True)