#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, ‎July ‎4, ‎2021, ‏‎19:42
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""


import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app


layout = html.Div([])


@app.callback()
def display_value(value):
    return 'You have selected "{}"'.format(value)