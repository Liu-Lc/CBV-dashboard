#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, July 6, 2021, 08:32
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""


from dash import dcc, html
import dash_table as table
import mysql.connector
import pandas as pd
from app import app
from dash.dependencies import Input, Output, State
from otros import keys


def isempty(field):
    return (field=='' or field==None)


header = html.Div([
            html.Link(rel="stylesheet",
                href="https://fonts.googleapis.com/css?family=Montserrat"),
            html.Link(rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"),
            html.Div(className='column', children=[
                html.H1('Formulario'),
                html.Hr()
            ]),
        ])

form =  html.Div(className='container', children=[
            html.Div(className='row', children=[
                html.Div(className='one-third column', children=[
                    html.Div(className='row', children=[
                        html.Span('Apellidos', className='label'),
                        html.Div(className='auto-column', children=[
                            dcc.Input(id='f-apellido1', className='input-style'),
                            dcc.Input(id='f-apellido2', className='input-style'),
                        ])
                    ]),
                    html.Div(className='row', children=[
                        html.Span('Nombre', className='label'),
                        dcc.Input(id='f-nombre', className='input-style'),
                    ]),
                    html.Div(className='row', children=[
                        html.Span('Cédula', className='label'),
                        dcc.Input(id='f-cedula', className='input-style'),
                    ]),
                    html.Div(className='row', children=[
                        html.Span('Fecha de nacimiento', className='label'),
                        dcc.DatePickerSingle(id='f-fechanac', className='input-style',
                            clearable=True, 
                        ),
                    ]),
                    html.P('', className='spacer'),
                    dcc.RadioItems(className='radio-items', id='search-option',
                        options=[
                            {'value':'ambigua', 'label':'Ambigua'},
                            {'value':'precisa', 'label':'Precisa'},
                            {'value':'exacta', 'label':'Exacta'},
                        ], value='exacta'
                    ),
                ]),
                ## Data Table
                html.Div(className='two-thirds column table', children=[
                    table.DataTable(id='table-buscar',
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
                ]),
            ]),
            html.Div(className='button-container', children=[
                html.Button('BUSCAR', id='button-buscar', className='large-button'),
                html.Button('LIMPIAR', id='button-limpiar1', className='large-button'),
                html.Button('MODIFICAR', id='button-modificar1', className='large-button'),
                html.Button('ELIMINAR', id='button-eliminar1', className='large-button'),
            ])
        ])

form_add =  html.Div(className='container', children=[
                html.Div(className='row', children=[
                    html.Div(className='one-third column', children=[
                        html.Div(className='row', children=[
                            html.Span('No.', className='label'),
                            dcc.Input(className='input-style'),
                        ]),
                        html.Div(className='row', children=[
                            html.Span('Apellidos', className='label'),
                            dcc.Input(className='input-style'),
                        ]),
                        html.Div(className='row', children=[
                            html.Span('Nombre', className='label'),
                            dcc.Input(className='input-style'),
                        ]),
                        html.Div(className='row', children=[
                            html.Span('Cédula', className='label'),
                            dcc.Input(className='input-style'),
                        ]),
                        html.Div(className='row', children=[
                            html.Span('Fecha de nacimiento', className='label'),
                            dcc.DatePickerSingle(id='fechanac2', className='input-style',
                                clearable=True, 
                            ),
                        ]),
                        html.P('', className='spacer'),
                    ]),
                    ## Data Table
                    html.Div(className='two-thirds column table', children=[
                        table.DataTable(id='table-agregar', 
                            columns=[
                                {'id':'apellido', 'name':'Apellido'},
                                {'id':'nombre', 'name':'Nombre'},
                                {'id':'cedula', 'name':'Cédula'},
                                {'id':'fecha_nac', 'name':'Fecha de nacimiento'},
                                {'id':'number', 'name':'No.'},
                            ],
                            fixed_rows={'headers': True},
                            # page_action='none',
                            page_size=150,
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
                    ]),
                ]),
                html.Div(className='button-container', children=[
                    html.Button('AGREGAR', id='button-agregar', className='large-button'),
                    html.Button('LIMPIAR', id='button-limpiar2', className='large-button'),
                    html.Button('MODIFICAR', id='button-modificar2', className='large-button'),
                    html.Button('ELIMINAR', id='button-eliminar2', className='large-button'),
                ]),
            ])

tabs =  dcc.Tabs(
            id="tabs-main",
            value='form',
            parent_className='tabs-container',
            className='tabs',
            content_className='tabs-content',
            children=[
                dcc.Tab(
                    label='Formulario',
                    value='form',
                    className='tab',
                    selected_className='tab-selected',
                    children=[form]
                ),
                dcc.Tab(
                    label='Agregar',
                    value='agregar',
                    className='tab',
                    selected_className='tab-selected',
                    children=[form_add]
                ),
            ]
        )


@app.callback(
    Output('table-buscar', 'data'),
    [Input('button-buscar', 'n_clicks')],
    [State('search-option', 'value'), State('f-apellido1', 'value'),
    State('f-apellido2', 'value'), State('f-nombre', 'value'), 
    State('f-cedula', 'value'), State('f-fechanac', 'value')]
)
def button_buscar_click(nclick, search_option, ap1, ap2, nom, ced, fnac):
    conn = mysql.connector.connect(**keys.config)
    query = ''; proc = ''; args = ()
    if ( not isempty(ap1) or not isempty(ap2) or
            not isempty(nom) and not isempty(ced) or 
            not isempty(fnac) ):
        if search_option=='ambigua':
            query = 'call'
            if not isempty(ap1) and isempty(ap2) and isempty(nom) and isempty(ced):
                ## apellido 1
                proc = 'B_1AP'
                args = (ap1, )
            elif not isempty(ap1) and not isempty(ap2) and isempty(nom) and isempty(ced) :
                ## apellido 2
                proc = 'B_2AP'
                args = (ap1, ap2)
            elif not isempty(ap1) and isempty(ap2) and not isempty(nom) and isempty(ced) :
                ## apellido 1 nombre
                proc = 'B_NOMAP1'
                args = (ap1, nom)
            elif not isempty(ap1) and not isempty(ap2) and not isempty(nom) and isempty(ced) :
                ## apellido 2 nombre
                proc = 'B_NOMAP2'
                args = (ap1, ap2, nom)
            elif not isempty(ced) :
                ## cedula
                proc = 'B_CED'
                args = (ced, )
            elif not isempty(fnac) :
                ## fecha
                proc = 'B_FECHA'
                args = (fnac, )
            else: pass
        elif search_option=='precisa':
            query = 'call'
            if not isempty(ap1) and isempty(ap2) and isempty(nom) and isempty(ced) :
                ## apellido 1
                proc = 'BUSCAR1AP'
                args = (ap1, )
            elif not isempty(ap1) and not isempty(ap2) and isempty(nom) and isempty(ced) :
                ## apellido 2
                proc = 'BUSCAR2AP'
                args = (ap1, ap2)
            elif not isempty(ap1) and isempty(ap2) and not isempty(nom) and isempty(ced) :
                ## apellido 1 nombre
                proc = 'BUSCARNOMAP1'
                args = (ap1, nom)
            elif not isempty(ap1) and not isempty(ap2) and not isempty(nom) and isempty(ced) :
                ## apellido 2 nombre
                proc = 'BUSCARNOMAP2'
                args = (ap1, ap2, nom)
            elif not isempty(ced) :
                ## cedula
                proc = 'BUSCARCED'
                args = (ced, )
            elif not isempty(fnac) :
                ## fecha
                proc = 'BUSCARFECHA'
                args = (fnac, )
            else: pass
        elif search_option=='exacta':
            q = []
            q.append('select * from clinica ')
            if ap1!=None and ap1!='': q.append(f''' APELLIDO like '%{ap1}%' ''')
            if ap2!=None and ap2!='': q.append(f''' APELLIDO like '%{ap2}%' ''')
            if nom!=None and nom!='': q.append(f''' NOMBRE like '%{nom}%' ''')
            if ced!=None and ced!='': q.append(f''' CEDULA like '%{ced}%' ''')
            if fnac!=None and fnac!='': q.append(f''' FECHA_NAC like '%{fnac}%' ''')
            query = q[0]
            if len(q)>0: query += '\nwhere' + '\nAND'.join(q[1:])
            query += '\norder by APELLIDO, NOMBRE; '
    
    if query!='':
        cursor = conn.cursor()
        if search_option=='exacta':
            cursor.execute(query)
            results = cursor.fetchall()
        else:
            cursor.callproc(proc, args)
            for result in cursor.stored_results():
                results = result.fetchall()
        cursor.close()
        conn.close()
        return pd.DataFrame(results, 
                columns=['id', 'apellido', 'nombre', 
                    'cedula', 'fecha_nac', 'number']).to_dict('records')
    else: return []

# @app.callback(
#     [Output('table-buscar', 'data'), Output('f-apellido1', 'value'),
#     Output('f-apellido2', 'value'), Output('f-nombre', 'value'), 
#     Output('f-cedula', 'value'), Output('f-fechanac', 'value')],
#     Input('button-limpiar1', 'n_clicks')
# )
# def clean_form(nclick):
#     return [], None, None, None, None, None