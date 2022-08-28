#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, July 4, 2021, 19:42
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""


from dash import dcc, html, dash_table as table
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
                    clearable=False, searchable=False, placeholder='Seleccione una opción...'),
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
                            page_size=150,
                            sort_action="native",
                            sort_mode="multi",
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
    Output('ver-option', 'options'), Output('ver-option', 'disabled'),
    Input('tabs-ver', 'value')
)
def display_options(tab):
    if tab=='todos':
        return [], True
    elif tab=='vacios':
        return [
            {'label':'Apellido', 'value':'APELLIDO'}, 
            {'label':'Nombre', 'value':'NOMBRE'}, 
            {'label':'Cédula', 'value':'CEDULA'}, 
            {'label':'Fecha de Nacimiento', 'value':'FECHA_NAC'},
            {'label':'Expediente', 'value':'NO'}
        ], False
    elif tab=='duplicados':
        return [
            {'label':'Apellido, Nombre y Cédula', 'value':'apnomced-dup'}, 
            {'label':'Apellido y Nombre', 'value':'apnom-dup'},
            {'label':'Cédula', 'value':'ced-dup'},
            {'label':'Expendiente', 'value':'exp-dup'}
        ], False
    # elif tab=='verificar':
    #     return [
    #         {'label':'', 'value':''}, 
    #     ], False

@app.callback(
    Output('table-ver', 'data'),
    Input('ver-option', 'value'),
    Input('tabs-ver', 'value')
)
def display_results(option, tab):
    results = []; query = ''
    conn = mysql.connector.connect(**keys.config)
    cursor = conn.cursor()
    if tab=='todos':
        query = '''select * from clinica order by ID desc; '''
    elif tab=='vacios' and option!=None:
        query = '''select * from clinica where %s = '' 
                    order by APELLIDO, NOMBRE; ''' % option
    elif tab=='duplicados' and option!=None:
        query = '''select * from clinica
            where concat({0}) in
                (select concat({0}) from clinica
                    group by {0} having {1}) {2}
            order by {0} {3};'''
        if option=='apnomced-dup':
            query = query.format('APELLIDO, NOMBRE, CEDULA', 
                'AND '.join(f'count({i})>1 '
                    for i in ['APELLIDO', 'NOMBRE', 'CEDULA']), '', 'asc')
        elif option=='apnom-dup':
            query = query.format('APELLIDO, NOMBRE', 
                'AND '.join(f'count({i})>1 ' 
                    for i in ['APELLIDO', 'NOMBRE']), '',  'asc')
        elif option=='ced-dup':
            query = query.format('CEDULA', 'count(CEDULA)>1', 
                "AND CEDULA!='' ",  'asc')
        elif option=='exp-dup':
            query = query.format('NO', 'count(NO)>1 ', '',  'desc')
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return pd.DataFrame(results, 
            columns=['id', 'apellido', 'nombre', 
                'cedula', 'fecha_nac', 'number']).to_dict('records')
    except:
        return []
    