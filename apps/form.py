#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, July 6, 2021, 08:32
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""


from dash import dcc, html, dash_table as table, callback_context as ctx
import dash_mantine_components as dmc
import mysql.connector
import pandas as pd
import os, sys, logging, datetime, json
from app import app
from dash.dependencies import Input, Output, State
from otros import keys


## Set up logging
LOG_FILE = os.getcwd() + "/logs"
if not os.path.exists(LOG_FILE):
    os.makedirs(LOG_FILE)
LOG_FILE = LOG_FILE + f"/log_{datetime.datetime.today().date()}.log"
logFormatter = logging.Formatter("%(levelname)s %(asctime)s %(message)s")
fileHandler = logging.FileHandler("{0}".format(LOG_FILE))
fileHandler.setFormatter(logFormatter)
stdout_handler = logging.StreamHandler(sys.stdout)
rootLogger = logging.getLogger()
rootLogger.addHandler(fileHandler)
rootLogger.addHandler(stdout_handler)
rootLogger.setLevel(logging.INFO)


def isempty(field):
    return (field=='' or field==None)

def fetch_sql(conn, query, fetch=1, buffer=True):
    try:
        cursor = conn.cursor(buffered=buffer)
        cursor.execute(query)
        if fetch==1: results = cursor.fetchone()
        else: results = cursor.fetchall()
        return results
    finally:
        conn.commit()
        cursor.close()
        conn.close()

def insert_sql(conn, table, columns='APELLIDO, NOMBRE, CEDULA, FECHA_NAC, NO', values=''):
    try:
        insert_query = f'''INSERT INTO %s ({columns}) VALUES({values});'''
        cursor = conn.cursor(buffered=True)
        cursor.execute(insert_query % table)
        return [True, cursor.lastrowid]
    except Exception as e:
        return [False, e]
    finally:
        conn.commit()
        cursor.close()
        conn.close()


def modify_sql(conn, table, id, apellido, nombre, cedula, fecha, exp):
    """ Executes update query on MySQL connection.

    Args:
        conn (mysql.connection): MySQL database connection
        table (string): table name
        id (int or string): record id to modify
        apellido (string): value
        nombre (string): value
        cedula (string): value
        fecha (string or datetime): value
        exp (int or string): value

    Returns:
        array: returns array with True or False value and an empty string or exception description respectively.
    """     
    try:
        update_query = f'''UPDATE {table} SET APELLIDO = UPPER('{apellido}'), 
            NOMBRE = UPPER('{nombre}'), CEDULA = '{cedula}', FECHA_NAC = '{fecha}',
            NO = {exp} WHERE ID = {id}; '''
        cursor = conn.cursor()
        cursor.execute(update_query)
        return [True, '']
    except Exception as e:
        return [False, e]
    finally:
        conn.commit()
        cursor.close()
        conn.close()


## Variable to initialize the complete form. Check styles for classNames.
form =  html.Div(className='container', children=[
            html.Div(className='row', children=[
                html.Div(className='one-third column', children=[
                    ## Starts the left panel with fields
                    html.Div(className='row', children=[
                        html.Span('Apellidos', className='label'),
                        html.Div(className='auto-column', children=[
                            dcc.Input(id='f-apellido1', className='input-style', autoComplete='off'),
                            dcc.Input(id='f-apellido2', className='input-style', autoComplete='off'),
                        ])
                    ]),
                    html.Div(className='row', children=[
                        html.Span('Nombre', className='label'),
                        dcc.Input(id='f-nombre', className='input-style', autoComplete='off'),
                    ]),
                    html.Div(className='row', children=[
                        html.Span('Cédula', className='label'),
                        dcc.Input(id='f-cedula', className='input-style', autoComplete='off'),
                    ]),
                    html.Div(className='row', children=[
                        html.Span('Fecha de nacimiento', className='label'),
                        dmc.DatePicker(id='f-fechanac', class_name='input-style', 
                            inputFormat='DD/MM/YYYY', clearable=True),
                    ]),
                    html.P('', className='spacer'),
                    ## Type of search radio selection
                    dcc.RadioItems(className='radio-items', id='search-option',
                        options=[
                            {'value':'ambigua', 'label':'Ambigua'},
                            {'value':'precisa', 'label':'Precisa'},
                            {'value':'exacta', 'label':'Exacta'},
                        ], value='exacta'
                    ),
                ]),
                ## Data Table for results in the right side
                html.Div(className='two-thirds column table', children=[
                    dcc.Loading(id='loading-table', type='default', children=[
                        table.DataTable(id='table-buscar',
                            columns=[
                                {'id':'id', 'name':'id'},
                                {'id':'apellido', 'name':'Apellido'},
                                {'id':'nombre', 'name':'Nombre'},
                                {'id':'cedula', 'name':'Cédula'},
                                {'id':'fecha_nac', 'name':'F. Nac.'},
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
            ]),
            ## Buttons section in lower section
            html.Div(className='button-container', children=[
                html.Button('BUSCAR', id='button-buscar', className='large-button'),
                html.Button('LIMPIAR', id='button-limpiar1', className='large-button'),
                html.Button('MODIFICAR', id='button-modificar1', className='large-button'),
                html.Button('ELIMINAR', id='button-eliminar1', className='large-button'),
            ])
        ])

form_modal = html.Div(children=[
    dmc.Modal([
        dmc.Title('Modificar Registro', order=3),
        html.P(className='spacer'),
        html.Div(className='modal-row', children=[
            html.Span('No.', className='label'),
            dcc.Input(className='input-style', id='modal-number', 
                type='number', autoComplete='off'),
        ]),
        html.P('', className='spacer'),
        html.Div(className='modal-row', children=[
            html.Span('Apellidos', className='label'),
            dcc.Input(className='input-style-m', id='modal-apellido', autoComplete='off'),
        ]),
        html.Div(className='modal-row', children=[
            html.Span('Nombre', className='label'),
            dcc.Input(className='input-style-m', id='modal-nombre', autoComplete='off'),
        ]),
        html.Div(className='modal-row', children=[
            html.Span('Cédula', className='label'),
            dcc.Input(className='input-style-m', id='modal-cedula', autoComplete='off'),
        ]),
        html.Div(className='modal-row', children=[
            html.Span('Fecha de nacimiento', className='label'),
            dmc.DatePicker(id='modal-fechanac', class_name='input-style',
                        inputFormat='DD/MM/YYYY')
            # dcc.DatePickerSingle(className='input-style-m', id='modal-fechanac', 
            #             display_format='DD/MM/YYYY'),
        ]),
        html.Div(className='button-container', children=[
            html.Button('MODIFICAR', id='button-modificar', className='large-button'),
            html.Button('RESTAURAR', id='button-restaurar', className='large-button'),
        ])
    ], id='modal', size='lg', centered=True, opened=False)
])

error_modal = html.Div([
    dmc.Modal([
        dmc.Title('Error', order=3),
        dmc.Text('')
    ], id='error-modal', size='md', centered=True, opened=False),
])

## Variable for adding records form
form_add =  html.Div(className='container', children=[
                dcc.ConfirmDialog(id='msg-empty-fields',
                     message='Faltan campos por rellenar'),
                html.Div(className='row', children=[
                    html.Div(className='one-third column', children=[
                        ## Left panel for fields
                        html.Div(className='row', children=[
                            html.Span('No.', className='label'),
                            html.Div(className='row', children=[
                                dcc.Input(id='a-number', type='number', className='input-style-s', autoComplete='off'),
                                html.Button(id='set-id-button', className='small-button', children=[
                                    html.I(className='fa fa-asterisk fa-xs'),
                                    # tooltip
                                    html.Span(className='tooltip', children=['Generar #']),
                                ]),
                                html.Button(id='check-id-button', className='small-button', children=[
                                    html.I(className='fa fa-check-circle fa-xs'),
                                    # tooltip
                                    html.Span(className='tooltip', children=['Verificar #']),
                                ]),
                            ]),
                        ]),
                        html.Div(className='row', children=[
                            html.Span('Apellidos', className='label'),
                            dcc.Input(className='input-style', id='a-apellido', autoComplete='off'),
                        ]),
                        html.Div(className='row', children=[
                            html.Span('Nombre', className='label'),
                            dcc.Input(className='input-style', id='a-nombre', autoComplete='off'),
                        ]),
                        html.Div(className='row', children=[
                            html.Span('Cédula', className='label'),
                            dcc.Input(className='input-style', id='a-cedula', autoComplete='off'),
                        ]),
                        html.Div(className='row', children=[
                            html.Span('Fecha de nacimiento', className='label'),
                            dmc.DatePicker(id='a-fechanac', class_name='input-style', 
                                inputFormat='DD/MM/YYYY', clearable=True),
                        ]),
                        html.P('', className='spacer'),
                    ]),
                    ## Data Table for results
                    html.Div(className='two-thirds column table', children=[
                        dcc.Loading(id='loading-table', type='default', children=[
                            table.DataTable(id='table-agregar', 
                                columns=[
                                    {'id':'id', 'name':'id'},
                                    {'id':'apellido', 'name':'Apellido'},
                                    {'id':'nombre', 'name':'Nombre'},
                                    {'id':'cedula', 'name':'Cédula'},
                                    {'id':'fecha_nac', 'name':'Fecha de nacimiento'},
                                    {'id':'number', 'name':'No.'},
                                ],
                                fixed_rows={'headers': True},
                                page_action='none',
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
                ]),
                ## Buttons section at lower side
                html.Div(className='button-container', children=[
                    html.Button('AGREGAR', id='button-agregar', className='large-button'),
                    html.Button('LIMPIAR', id='button-limpiar2', className='large-button'),
                    html.Button('MODIFICAR', id='button-modificar2', className='large-button', disabled=True),
                    html.Button('ELIMINAR', id='button-eliminar2', className='large-button', disabled=True),
                ]),
            ])

## Adding a tab container to switch between the searching form and adding form
tabs =  html.Div(className='column', children=[
            dcc.Tabs(
                id="tabs-main",
                value='form',
                parent_className='tabs-container',
                className='tabs',
                content_className='tabs-content',
                children=[
                    dcc.Tab(
                        ## Tab for searching
                        label='Formulario',
                        value='form',
                        className='tab',
                        selected_className='tab-selected',
                        children=[form] ## Form variable
                    ),
                    dcc.Tab(
                        label='Agregar',
                        value='agregar',
                        className='tab',
                        selected_className='tab-selected',
                        children=[form_add] ## Add form variable
                    ),
                ]
            ),
            form_modal,
            error_modal
        ])


## Callbacks / Actions / Updates
@app.callback(
    ## App callback to bring results to table when pressing search button
    [Output('table-buscar', 'data'), Output('f-apellido1', 'value'),
    Output('f-apellido2', 'value'), Output('f-nombre', 'value'), 
    Output('f-cedula', 'value'), Output('f-fechanac', 'value'),],
    [Input('button-buscar', 'n_clicks'), Input('button-limpiar1', 'n_clicks'),],
    # Takes data from textboxes
    [State('search-option', 'value'), State('f-apellido1', 'value'),
    State('f-apellido2', 'value'), State('f-nombre', 'value'), 
    State('f-cedula', 'value'), State('f-fechanac', 'date')]
)
def search_tab(search_click, clean_click, search_option, ap1, ap2, nom, ced, fnac):
    triggered_id = ctx.triggered_id
    if triggered_id=='button-limpiar1' or triggered_id==None:
        return [], '', '', '', '', ''
    elif triggered_id=='button-buscar':
        # mysql connection
        conn = mysql.connector.connect(**keys.config)
        # Initialize variables
        query = ''; proc = ''; args = ()
        ## Searching for any last name, first name, ID or birthdate.
        if ( not isempty(ap1) or not isempty(ap2) or
                not isempty(nom) and not isempty(ced) or 
            not isempty(nom) and not isempty(ced) or 
                not isempty(nom) and not isempty(ced) or 
                not isempty(fnac) ):
            ## Switching between search option selection
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
                # Appends sentence depending on fields with contents
                if ap1!=None and ap1!='': q.append(f''' APELLIDO like '%{ap1}%' ''')
                if ap2!=None and ap2!='': q.append(f''' APELLIDO like '%{ap2}%' ''')
                if nom!=None and nom!='': q.append(f''' NOMBRE like '%{nom}%' ''')
                if ced!=None and ced!='': q.append(f''' CEDULA like '%{ced}%' ''')
                if fnac!=None and fnac!='': q.append(f''' FECHA_NAC like '%{fnac}%' ''')
                query = q[0]
                if len(q)>0: query += '\nwhere' + '\nAND'.join(q[1:])
                query += '\norder by APELLIDO, NOMBRE; '
        
        # After creating the query, cursor is created
        if query!='':
            cursor = conn.cursor()
            # Executes query or procedure depending of search option
            if search_option=='exacta':
                cursor.execute(query)
                results = cursor.fetchall()
            else:
                cursor.callproc(proc, args)
                for result in cursor.stored_results():
                    results = result.fetchall()
            cursor.close()
            conn.close()
            ## Returns results in a dataframe to output object that is the DataTable
            return [pd.DataFrame(results, 
                    columns=['id', 'apellido', 'nombre', 
                    'cedula', 'fecha_nac', 'direccion', 'number']).to_dict('records'), 
                    ap1, ap2, nom, ced, fnac]
        else: return [], ap1, ap2, nom, ced, fnac
    return [], ap1, ap2, nom, ced, fnac


@app.callback(
    ## App callback to add a record
    [Output('table-agregar', 'data'), Output('a-apellido', 'value'),
    Output('a-nombre', 'value'), Output('a-cedula', 'value'), 
    Output('a-fechanac', 'value'), Output('a-number', 'value'), 
    Output('a-number', 'className'), Output('msg-empty-fields', 'displayed'),
    Output('msg-empty-fields', 'message')],
    [Input('check-id-button', 'n_clicks'), Input('set-id-button', 'n_clicks'), 
    Input('button-agregar', 'n_clicks'), Input('button-limpiar2', 'n_clicks'),
    Input('tabs-main', 'value')],
    [State('table-agregar', 'data'), State('a-apellido', 'value'), 
    State('a-nombre', 'value'), State('a-cedula', 'value'), 
    State('a-fechanac', 'date'), State('a-number', 'value'), 
    State('a-number', 'className'), State('msg-empty-fields', 'message')]
)
def add_tab(check_click, set_click, add_button, clear_button, tab, data, ap, nom, ced, fnac, number, num_class, message):
    config = json.load(open('assets/config.json'))
    triggered_id = ctx.triggered_id
    if triggered_id=='check-id-button' and check_click!=None:
        ### Check number id button if already exists
        try:
            results = fetch_sql(mysql.connector.connect(**keys.config),
                f'SELECT NO FROM clinica WHERE NO={number}')
        except: return data, ap, nom, ced, fnac, number, 'input-style-s', True, 'Error: No connection.'
        if results==None:
            return data, ap, nom, ced, fnac, number, 'input-style-s input-green', False, message
        else:
            return data, ap, nom, ced, fnac, number, 'input-style-s input-red', False, message
    elif triggered_id=='set-id-button' and set_click!=None:
        ### Set id button generates a new number by adding 1 to the max number
        results = fetch_sql(mysql.connector.connect(**keys.config), 
                    f'SELECT MAX(NO) FROM clinica')
        if results==None:
            return data, ap, nom, ced, fnac, '', num_class, False, message
        else:
            return data, ap, nom, ced, fnac, results[0]+1, num_class, False, message
    elif triggered_id=='button-agregar':
        ### Pressing add button
        # check if all fields are complete
        if ( isempty(ap) or isempty(nom) or isempty(ced) or isempty(fnac) or isempty(number) ):
            # Returns True to displayed message for empty fields
            return data, ap, nom, ced, fnac, number, num_class, True, 'Faltan campos por rellenar.'
        else:
            # If the fields are complete, then add to database
            try:
                results = fetch_sql(mysql.connector.connect(**keys.config), 
                        f'''SELECT * FROM clinica WHERE (APELLIDO = '{ap}' AND NOMBRE = '{nom}') 
                        AND (CEDULA = '{ced}' AND CEDULA != '') OR NO = '{number}';''')
            except:
                return data, ap, nom, ced, fnac, number, num_class, True, 'Error: No connection.'
            if results==None: # If the select statement returns None, means theres no similar record
                # Can be added
                # insert_query = f'''INSERT INTO %s (APELLIDO, NOMBRE, CEDULA, FECHA_NAC, NO) VALUES('{ap}', '{nom}', '{ced}', '{fnac}', {number});'''
                try:
                    values = f''' '{ap}', '{nom}', '{ced}', '{fnac}', {number}'''
                    result1, e = insert_sql(mysql.connector.connect(**keys.config),
                        'clinica', values=values)
                    if result1:
                        result2, e = insert_sql(mysql.connector.connect(**keys.config),
                            columns=''' ID, TRANSACTION, APELLIDO, NOMBRE, CEDULA, FECHA_NAC, NO ''',
                            table='movements', values=f''' {e}, 'ADD',''' + values)
                        if not result2: raise e
                    else: raise e
                    results = [None, '', '', '', None, '', num_class, False, '']
                except Exception as e:
                    print(f'Error inserting. {e}')
                    return (data, ap, nom, ced, fnac, number, num_class, True, 'Error has ocurred.')
            else:
                # Cannot be added because there's already a similar record
                return (data, ap, nom, ced, fnac, number, num_class, True, 
                'Error. Existe un registro con el mismo número de cédula y/o expediente.')
            ## If the record was added succesfully then the datatable has to be updated
            try:
                data = fetch_sql(mysql.connector.connect(**keys.config), fetch=2,
                    query=f'''SELECT * FROM movements WHERE No>{config['last_num']} AND TRANSACTION='ADD';''')
                # results = (data, ap, nom, ced, fnac, number, num_class, False, '')
                results = [pd.DataFrame(data, columns=['id', 'transaction', 'apellido', 'nombre', 
                    'cedula', 'fecha_nac', 'direccion', 'number']).to_dict('records'), 
                    '', '', '', None, '', num_class, False, '']
            except Exception as e:
                print(f'Error updating data table. {e}')
                return [data, ap, nom, ced, fnac, number, num_class, True, 'Error has ocurred.']
            return results
    elif triggered_id=='button-limpiar2':
        results = fetch_sql(mysql.connector.connect(**keys.config),
            f'''SELECT MAX(No) FROM movements WHERE TRANSACTION='ADD';''')
        # Create dictionary variable with max number
        config = {'last_num':results[0]}
        # Dump json of dictionary into config file
        json.dump(config, open('assets/config.json', 'w'))
        # drop everything from table added
        return None, None, None, None, None, None, num_class, False, message
    elif triggered_id=='tabs-main':
        if tab=='agregar':
            results = fetch_sql(mysql.connector.connect(**keys.config), fetch=2,
                query=f'''SELECT * FROM movements WHERE No>{config['last_num']};''')
            if results==None:
                return [[], None, None, None, None, None, num_class, False, message]
            else:
                return [pd.DataFrame(results, columns=['id', 'transaction', 'apellido', 'nombre', 
                    'cedula', 'fecha_nac', 'direccion', 'number']).to_dict('records'), 
                    None, None, None, None, None, num_class, False, message]
    return data, ap, nom, ced, fnac, number, num_class, False, message


@app.callback(
    [Output('modal', 'opened'), Output('modal-number', 'value'),
    Output('modal-apellido', 'value'), Output('modal-nombre', 'value'),
    Output('modal-cedula', 'value'), Output('modal-fechanac', 'value')],
    [Input('button-modificar1', 'n_clicks'), Input('button-restaurar', 'n_clicks')],
    [State('modal', 'opened'), State('table-buscar', 'active_cell'), 
    State('table-buscar', 'data'), ]
)
def show_modificar(form_open, restaurar, is_open, cell, rows):
    triggered_id = ctx.triggered_id
    if triggered_id=='button-restaurar':
        # Restore the value to original
        data = pd.DataFrame(rows, columns=['id', 'apellido', 'nombre', 
                    'cedula', 'fecha_nac', 'number'])
        row = data[data.id==cell['row_id']].squeeze()
        return is_open, row.number, row.apellido, row.nombre, row.cedula, row.fecha_nac
    else:
        # When the modal initializates
        if form_open and cell!=None:
            data = pd.DataFrame(rows, columns=['id', 'apellido', 'nombre', 
                            'cedula', 'fecha_nac', 'number'])
            row = data[data.id==cell['row_id']].squeeze()
            # Shows the information from the selected row into the modal
            return not is_open, row.number, row.apellido, row.nombre, row.cedula, row.fecha_nac
    return is_open, None, None, None, None, None

