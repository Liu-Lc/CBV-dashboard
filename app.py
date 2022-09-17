#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, July 4, 2021, 18:34
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""

import dash
import dash_auth
from otros.users import USERNAME_PASSWORD_PAIRS

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD_PAIRS)