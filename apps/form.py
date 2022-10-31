#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, July 6, 2021, 08:32
@author: Lucia Liu (liu.lc.ch@gmail.com)
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

## Variables
config_file = 'otros/config.json'


def isempty(field):
    return (field=='' or field==None)

def generate_search_query(search_option:str, ap1, ap2, nom, ced, fnac:datetime):
    """ Generates the query or procedure call command to search a record depending on the type of search option.

    Args:
        search_option (str): type of search
        ap1 (string): first surname
        ap2 (string): second surname
        nom (string): name
        ced (string): personal identification number
        fnac (datetime): birth date

    Returns:
        array: array with query, procedure call and arguments variables.
    """    
    query = ''; proc = ''; args = ()
    ## Searching for any last name, first name, ID or birthdate.
    if ( not isempty(ap1) or not isempty(ap2) or not isempty(ced)
            or not isempty(ced) or not isempty(nom) or not isempty(fnac) ):
        ## Switching between search option selection
        if search_option=='ambigua':
            query = 'call'
            if not isempty(ap1) and isempty(ap2) and isempty(nom) and isempty(ced): ## apellido 1
                proc = 'B_1AP'; args = (ap1, )
            elif not isempty(ap1) and not isempty(ap2) and isempty(nom) and isempty(ced): ## apellido 2
                proc = 'B_2AP'; args = (ap1, ap2)
            elif not isempty(ap1) and isempty(ap2) and not isempty(nom) and isempty(ced): ## apellido 1 nombre
                proc = 'B_NOMAP1'; args = (ap1, nom)
            elif not isempty(ap1) and not isempty(ap2) and not isempty(nom) and isempty(ced): ## apellido 2 nombre
                proc = 'B_NOMAP2'; args = (ap1, ap2, nom)
            elif not isempty(ced): ## cedula
                proc = 'B_CED'; args = (ced, )
            elif not isempty(fnac): ## fecha
                proc = 'B_FECHA'; args = (fnac, )
            else: pass
        elif search_option=='precisa':
            query = 'call'
            if not isempty(ap1) and isempty(ap2) and isempty(nom) and isempty(ced): ## apellido 1
                proc = 'BUSCAR1AP'; args = (ap1, )
            elif not isempty(ap1) and not isempty(ap2) and isempty(nom) and isempty(ced): ## apellido 2
                proc = 'BUSCAR2AP'; args = (ap1, ap2)
            elif not isempty(ap1) and isempty(ap2) and not isempty(nom) and isempty(ced): ## apellido 1 nombre
                proc = 'BUSCARNOMAP1'; args = (ap1, nom)
            elif not isempty(ap1) and not isempty(ap2) and not isempty(nom) and isempty(ced):  ## apellido 2 nombre
                proc = 'BUSCARNOMAP2'; args = (ap1, ap2, nom)
            elif not isempty(ced): ## cedula
                proc = 'BUSCARCED'; args = (ced, )
            elif not isempty(fnac): ## fecha
                proc = 'BUSCARFECHA'; args = (fnac, )
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
    return query, proc, args

def fetch_sql(conn, query, fetch=1, buffer=True):
    try:
        cursor = conn.cursor(buffered=buffer)
        cursor.execute(query)
        if fetch==1: results = cursor.fetchone()
        else: results = cursor.fetchall()
        return True, results
    except Exception as e:
        return False, e
    finally:
        conn.commit()
        cursor.close()
        conn.close()

def insert_sql(conn, table, **kwargs):
    """ Inserts values into provided MySQL connection, table and arguments (columns and values).

    Args:
        conn (mysql.connection): MySQL connection
        table (string): table name
        **ID (int): id
        **APELLIDO (string): last name
        **NOMBRE (string): name
        **CEDULA (string): identification number
        **FECHA_NAC (string or date): birth date
        **NO (int): record number
        **TRANSACTION (string): transaction type
        **DATEADDED (string or datetime): datetime added
        **kwargs: additional columns

    Returns:
        array: returns boolean if succesfull, last row id if true and exception if false.
    """    
    columns = ', '.join(kwargs.keys())
    values = ', '.join(repr(x) if x else 'NULL' for x in kwargs.values() )
    try:
        insert_query = f'''INSERT INTO {table} ({columns}) VALUES({values});'''
        cursor = conn.cursor(buffered=True)
        cursor.execute(insert_query)
        return [True, cursor.lastrowid]
    except Exception as e:
        return [False, e]
    finally:
        conn.commit()
        cursor.close()
        conn.close()

def modify_sql(conn, table, values:dict, conditions:dict):
    """ Executes update query on provided MySQL connection.

    Args:
        conn (mysql.connection): MySQL database connection
        table (string): table name
        values (dict): dictionary with the values to modify
        conditions (dict): conditions of the value to modify

    Returns:
        array: returns array with True or False value and an empty string or exception description respectively.
    """
    sets = ', '.join( [f'{key} = {repr(value)}' for key, value in values.items()]  )
    where = ' AND '.join( [f'{key} = {repr(value)}' for key, value in conditions.items()]  )
    try:
        update_query = f'''UPDATE {table} SET {sets} WHERE {where}; '''
        cursor = conn.cursor()
        cursor.execute(update_query)
        return [True, '']
    except Exception as e:
        return [False, e]
    finally:
        conn.commit()
        cursor.close()
        conn.close()

def delete_sql(conn, table, id:int, transaction:bool=False):
    """ Executes delete statement on MySQL connection provided.

    Args:
        conn (mysql.connector): MySQL connection
        table (str): table name
        id (int): record's ID to delete

    Returns:
        array: True of False if the statement executed. If false, additionally returns exception.
    """    
    try:
        delete_query = f'''DELETE FROM {table} WHERE ID = {id} 
            {"AND TRANSACTION='ADD'" if transaction else ''}; '''
        cursor = conn.cursor()
        cursor.execute(delete_query)
        return [True, '']
    except Exception as e:
        return [False, e]
    finally:
        conn.commit()
        cursor.close()
        conn.close()


## Variable to initialize the complete form. Check styles for classNames.
form =  html.Div(className='container', children=[
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
                html.P('', className='spacer'),
                ## Buttons section in lower section
                html.Div(className='column', children=[
                    html.Div(className='row', children=[
                        html.Button('BUSCAR', id='button-buscar', className='large-button'),
                        html.Button('LIMPIAR', id='button-limpiar1', className='large-button'),
                    ]),
                    html.Div(className='row', children=[
                        dcc.ConfirmDialog(id='msg-eliminar'),
                        html.Button('MODIFICAR', id='button-modificar1', className='large-button'),
                        html.Button('ELIMINAR', id='button-eliminar1', className='large-button'),
                    ]),
                ]),
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
                        style_table={'height': '420px', 'overflowY': 'auto'},
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
        ])

form_modal = html.Div(children=[
        dmc.Modal([
            dcc.Loading(id='loading-mod-modal', type='default', children=[
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
                ]),
                html.Div(className='button-container', children=[
                    html.Button('RESTAURAR', id='button-restaurar', className='large-button'),
                    html.Button('MODIFICAR', id='button-modificar', className='large-button'),
                ])
            ])
        ], id='modal', size='lg', centered=True, opened=False)
])

add_modal = html.Div(children=[
        dmc.Modal([
            dcc.Loading(id='loading-mod-modal2', type='default', children=[
                dmc.Title('Modificar Registro', order=3),
                html.P(className='spacer'),
                html.Div(className='modal-row', children=[
                    html.Span('No.', className='label'),
                    dcc.Input(className='input-style', id='modal-number2', 
                        type='number', autoComplete='off'),
                ]),
                html.P('', className='spacer'),
                html.Div(className='modal-row', children=[
                    html.Span('Apellidos', className='label'),
                    dcc.Input(className='input-style-m', id='modal-apellido2', autoComplete='off'),
                ]),
                html.Div(className='modal-row', children=[
                    html.Span('Nombre', className='label'),
                    dcc.Input(className='input-style-m', id='modal-nombre2', autoComplete='off'),
                ]),
                html.Div(className='modal-row', children=[
                    html.Span('Cédula', className='label'),
                    dcc.Input(className='input-style-m', id='modal-cedula2', autoComplete='off'),
                ]),
                html.Div(className='modal-row', children=[
                    html.Span('Fecha de nacimiento', className='label'),
                    dmc.DatePicker(id='modal-fechanac2', class_name='input-style',
                                inputFormat='DD/MM/YYYY')
                ]),
                html.Div(className='button-container', children=[
                    html.Button('RESTAURAR', id='button-restaurar-mod', className='large-button'),
                    html.Button('MODIFICAR', id='button-modificar-mod', className='large-button'),
                ])
            ])
        ], id='modal2', size='lg', centered=True, opened=False)
])

error_modal = html.Div([
    dmc.Modal([
        dmc.Title('Error', order=3),
        dmc.Text('', id='error-modal-text')
    ], id='error-modal', size='md', centered=True, opened=False),
])

## Variable for adding records form
form_add =  html.Div(className='container', children=[
                dcc.ConfirmDialog(id='msg-empty-fields',
                     message='Faltan campos por rellenar'),
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
                    ## Buttons section at lower side
                    html.Div(className='column', children=[
                        html.Div(className='row', children=[
                            html.Button('AGREGAR', id='button-agregar', className='large-button'),
                            html.Button('LIMPIAR', id='button-limpiar2', className='large-button'),
                        ]),
                        html.Div(className='row', children=[
                            dcc.ConfirmDialog(id='msg-eliminar2'),
                            html.Button('MODIFICAR', id='button-modificar2', className='large-button'),
                            html.Button('ELIMINAR', id='button-eliminar2', className='large-button'),
                        ]),
                    ]),
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
                                {'id':'fecha_nac', 'name':'F. Nac'},
                                {'id':'number', 'name':'No.'},
                            ],
                            sort_by=[{'column_id':'id', 'direction':'desc'}],
                            fixed_rows={'headers': True},
                            page_action='none',
                            page_size=150,
                            style_table={'height': '420px', 'overflowY': 'auto'},
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
            form_modal, add_modal, error_modal
        ])


## Callbacks / Actions / Updates ##

## App callback to bring results to table when pressing search button
@app.callback(
    [Output('table-buscar', 'data'), # Datatable results
    # Form fields
    Output('f-apellido1', 'value'), Output('f-apellido2', 'value'), 
    Output('f-nombre', 'value'), Output('f-cedula', 'value'), 
    Output('f-fechanac', 'value'),
    # Modify modal
    Output('modal', 'opened'), 
    # Error modal
    Output('error-modal', 'opened'), Output('error-modal-text', 'children'),
    # Modify modal fields
    Output('modal-number', 'value'), Output('modal-apellido', 'value'), 
    Output('modal-nombre', 'value'), Output('modal-cedula', 'value'), 
    Output('modal-fechanac', 'value'),
    # Output for confirm dialog
    Output('msg-eliminar', 'displayed'), Output('msg-eliminar', 'message')],
    ## INPUTS
    [Input('button-buscar', 'n_clicks'), Input('button-limpiar1', 'n_clicks'),
    Input('button-modificar', 'n_clicks'),
    # Modal inputs
    Input('button-modificar1', 'n_clicks'), Input('button-restaurar', 'n_clicks'),
    # Confirm dialog for remove record
    Input('button-eliminar1', 'n_clicks'), Input('msg-eliminar', 'submit_n_clicks')],
    ## STATES
    [State('search-option', 'value'), State('f-apellido1', 'value'),
    State('f-apellido2', 'value'), State('f-nombre', 'value'), 
    State('f-cedula', 'value'), State('f-fechanac', 'value'),
    # Modal states
    State('modal', 'opened'), 
    State('modal-apellido', 'value'), State('modal-nombre', 'value'), 
    State('modal-cedula', 'value'), State('modal-fechanac', 'value'),
    State('modal-number', 'value'), 
    # Datatable States
    State('table-buscar', 'data'), State('table-buscar', 'active_cell')]
)
def search_tab(search_click, clean_click, modify_click, modificar, restaurar, show_eliminar, eliminar, search_option, ap1, ap2, nom, ced, fnac, m_open, m_ap, m_nom, m_ced, m_fnac, m_num, buscar_data, cell):
    triggered_id = ctx.triggered_id
    modified = False
    ## put modify first with a separate if and use variable to control context trigger
    if triggered_id=='button-modificar':
        ## Update table for modificar action
        if ( isempty(m_ap) or isempty(m_nom) or isempty(m_ced) or isempty(m_fnac) or isempty(m_num) ):
            # Show modal error
            return [ buscar_data, ap1, ap2, nom, ced, fnac, m_open, True,
                'Error. Faltan campos por rellenar.', None, None, None, None, None,
                False, '']
        else:
            ## Check if values are already in the database
            bol, results = fetch_sql(mysql.connector.connect(**keys.config),
                f'''SELECT * FROM clinica WHERE ID != {cell['row_id']}
                    AND ( (APELLIDO = UPPER('{m_ap}') AND NOMBRE = UPPER('{m_nom}') ) 
                        OR (CEDULA = UPPER('{m_ced}') AND CEDULA != '') OR NO = '{m_num}');''')
            if bol and results==None:
                ## Can be modified
                modify, e = modify_sql(mysql.connector.connect(**keys.config),
                    'clinica', values={'APELLIDO':m_ap, 'NOMBRE':m_nom, 'CEDULA':m_ced, 
                        'FECHA_NAC':m_fnac, 'NO':m_num}, conditions={'ID':cell['row_id']} )
                modify2, e = modify_sql(mysql.connector.connect(**keys.config),
                    'movements', values={'APELLIDO':m_ap, 'NOMBRE':m_nom, 'CEDULA':m_ced, 
                        'FECHA_NAC':m_fnac, 'NO':m_num}, 
                    conditions={'ID':cell['row_id'], 'TRANSACTION':'ADD'} )
                if modify: 
                    modified = True ## Record modified
                    if modify2: logging.info(f'''[Movements] Record {cell['row_id']} succesfully modified.''')
                    else: logging.error(f'''[Movements] Error updating record {cell['row_id']}.''')
                    data = pd.DataFrame(buscar_data, columns=['id', 'apellido', 'nombre', 
                            'cedula', 'fecha_nac', 'number'])
                    row = data[data.id==cell['row_id']].squeeze()
                    ## Adding insert query with modified into movements
                    time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    modify_mov, modify_e = insert_sql(mysql.connector.connect(**keys.config), 'movements',
                            ID=cell['row_id'], TRANSACTION='MODIFY', DATEADDED=time_now, 
                            APELLIDO=row.apellido.upper(), NOMBRE=row.nombre.upper(), 
                            CEDULA=row.cedula.upper(), FECHA_NAC=row.fecha_nac, NO=row.number)
                    if modify_mov: 
                        logging.info(f'''[Clinica] Record {cell['row_id']} succesfully modified.''')
                    else: 
                        logging.exception(f'''[Movements] Error adding record {cell['row_id']}. Exception: {modify_e}''')
                    # In this step, the condition doesnt return thus jumps to search condition
                else: 
                    logging.exception(f'''[Clinica] Error modifying record {cell['row_id']}.\nException: {e}''')
                    return [ buscar_data, ap1, ap2, nom, ced, fnac, m_open, True, f'Error modificando el registro.', 
                        None, None, None, None, None, False, '']
            else: 
                return [ buscar_data, ap1, ap2, nom, ced, fnac, m_open, True,
                    f'Error. Ya existe un registro similar: \n{results}.', None, None, None, 
                    None, None, False, '']
    elif triggered_id=='msg-eliminar':
        data = pd.DataFrame(buscar_data, columns=['id', 'apellido', 'nombre', 
                'cedula', 'fecha_nac', 'number'])
        row = data[data.id==cell['row_id']].squeeze()
        time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        add_del_mov, add_del_e = insert_sql(mysql.connector.connect(**keys.config), 'movements',
                        ID=cell['row_id'], TRANSACTION='DELETE', DATEADDED=time_now, 
                        APELLIDO=row.apellido.upper(), NOMBRE=row.nombre.upper(), 
                        CEDULA=row.cedula.upper(), FECHA_NAC=row.fecha_nac, NO=row.number)
        if add_del_mov: 
            logging.info(f'''[Movements] Record {cell['row_id']} succesfully added.''')
            # Delete from tables
            delete_mov, delete_e = delete_sql(mysql.connector.connect(**keys.config), 'clinica', cell['row_id'])
            delete_mov2, delete_e2 = delete_sql(mysql.connector.connect(**keys.config), 
                                        'movements', cell['row_id'], transaction=True)
            if delete_mov: 
                modified = True
                logging.info(f'''[Clinica] Record {cell['row_id']} succesfully deleted.''')
            else: 
                logging.exception(f'''[Clinica] Error deleting record {cell['row_id']}. Exception: {delete_e}''')
                return [ buscar_data, ap1, ap2, nom, ced, fnac, m_open, True,
                    f'Error eliminando el registro.', None, None, None, None, None, False, '']
            if not delete_mov2: 
                logging.exception(f'''[Movements] Error deleting record {cell['row_id']}. Exception: {delete_e2}''')
        else: logging.exception(f'''[Movements] Error adding record [{row}].\nException: {add_del_e}''')

    ### If its modified, then it will jump to this condition ###
    if triggered_id=='button-buscar' or modified:
        # mysql connection
        conn = mysql.connector.connect(**keys.config)
        # Generate query or procedure call
        query, proc, args = generate_search_query(search_option, ap1, ap2, nom, ced, fnac)
        # After creating the query, cursor is created
        if query!='':
            cursor = conn.cursor()
            # Executes query or procedure depending of search option
            try:
                if search_option=='exacta':
                    cursor.execute(query)
                    results = cursor.fetchall()
                else:
                    cursor.callproc(proc, args)
                    for result in cursor.stored_results():
                        results = result.fetchall()
                ## Returns results in a dataframe to output object that is the DataTable
                return [pd.DataFrame(results, columns=['id', 'apellido', 'nombre', 
                    'cedula', 'fecha_nac', 'direccion', 'number']).to_dict('records'), 
                    ap1, ap2, nom, ced, fnac, False, False, '', None, None, None, None, None,
                    False, '']
            except Exception as e:
                logging.exception(f'''Error searching record. Exception: {e}''')
                error_text = f'Error: {e}'
                return [[], ap1, ap2, nom, ced, fnac, False, True, error_text, None, None, None, 
                None, None, False, '']
            finally:
                cursor.close()
                conn.close()
        else: return [buscar_data, ap1, ap2, nom, ced, fnac, False, False, '', None, None, None, 
            None, None, False, '']
    elif triggered_id=='button-limpiar1' or triggered_id==None:
        return [], '', '', '', '', '', False, False, '', None, None, None, None, None, False, ''
    elif triggered_id=='button-modificar1' or triggered_id=='button-restaurar':
        if cell!=None and len(buscar_data)>0:
            data = pd.DataFrame(buscar_data, columns=['id', 'apellido', 'nombre', 
                            'cedula', 'fecha_nac', 'number'])
            row = data[data.id==cell['row_id']].squeeze()
            # modal open return value depending on callback trigger
            open_value = m_open if triggered_id=='button-restaurar' else not m_open
            # Shows the information from the selected row into the modal
            return [buscar_data, ap1, ap2, nom, ced, fnac, open_value, False, '',  
                row.number, row.apellido, row.nombre, row.cedula, row.fecha_nac, False, '']
    elif triggered_id=='button-eliminar1' and cell!=None and len(buscar_data)>0:
        # Button from main tab that shows a message box (msg-eliminar)
        data = pd.DataFrame(buscar_data, columns=['id', 'apellido', 'nombre', 
                'cedula', 'fecha_nac', 'number'])
        if cell['row_id'] in data.id.values:
            row = data[data.id==cell['row_id']].squeeze()
            return [buscar_data, ap1, ap2, nom, ced, fnac, False, False, '', None, None, None, 
                None, None, True, 
                f'Seguro desea eliminar el siguiente registro?\nNombre: {row.apellido}, {row.nombre}\nExpediente: {row.number}']
        else: return [buscar_data, ap1, ap2, nom, ced, fnac, False, False, '', None, None, None, 
                None, None, True, 
                f'Error. Por favor vuelva a seleccionar otra casilla del registro.']
    return [buscar_data, ap1, ap2, nom, ced, fnac, False, False, '', 
        None, None, None, None, None, False, '']
    ## datatable, ap1, ap2, nom, ced, fnac, modal open, error-modal open, error-modal-text, modal-number, modal-apellido, modal-nombre, modal-cedula, modal-fechanac


## App callback to add a record
@app.callback(
    [Output('table-agregar', 'data'), # Datatable results
    # Add tab fields
    Output('a-apellido', 'value'), Output('a-nombre', 'value'), 
    Output('a-cedula', 'value'), Output('a-fechanac', 'value'), 
    Output('a-number', 'value'), Output('a-number', 'className'), 
    # Message box
    Output('msg-empty-fields', 'displayed'), Output('msg-empty-fields', 'message'),
    # Modify modal
    Output('modal2', 'opened'),
    # Modify modal fields
    Output('modal-number2', 'value'), Output('modal-apellido2', 'value'), 
    Output('modal-nombre2', 'value'), Output('modal-cedula2', 'value'), 
    Output('modal-fechanac2', 'value'),
    # Output for confirm dialog
    Output('msg-eliminar2', 'displayed'), Output('msg-eliminar2', 'message')],
    ## INPUTS
    # Small buttons
    [Input('check-id-button', 'n_clicks'), Input('set-id-button', 'n_clicks'), 
    # Main buttons
    Input('button-agregar', 'n_clicks'), Input('button-limpiar2', 'n_clicks'),
    Input('button-modificar2', 'n_clicks'), 
    # Modal inputs
    Input('button-modificar-mod', 'n_clicks'), Input('button-restaurar-mod', 'n_clicks'),
    # Remove records
    Input('button-eliminar2', 'n_clicks'), Input('msg-eliminar2', 'submit_n_clicks'),
    # Tab
    Input('tabs-main', 'value')],
    ## STATES
    [State('table-agregar', 'data'), State('table-agregar', 'active_cell'),
    # Fields
    State('a-apellido', 'value'), State('a-nombre', 'value'), 
    State('a-cedula', 'value'), State('a-fechanac', 'value'), 
    State('a-number', 'value'), 
    # Modal states
    State('modal2', 'opened'), 
    State('modal-apellido2', 'value'), State('modal-nombre2', 'value'), 
    State('modal-cedula2', 'value'), State('modal-fechanac2', 'value'),
    State('modal-number2', 'value'), 
    # Style and message
    State('a-number', 'className'), State('msg-empty-fields', 'message')]
)
def add_tab(check_click, set_click, add_button, clear_button, modificar_button, mod_modificar, mod_restaurar, eliminar_button, msg_eliminar, tab, add_data, cell, ap, nom, ced, fnac, number, m_open, m_ap, m_nom, m_ced, m_fnac, m_num, num_class, message):
    config = json.load(open(config_file))
    triggered_id = ctx.triggered_id
    modified = False
    if triggered_id=='button-agregar':
        ### Pressing add button. First check if all fields are complete
        if ( isempty(ap) or isempty(nom) or isempty(ced) or isempty(fnac) or isempty(number) ):
            # Returns True to displayed message for empty fields
            return [add_data, ap, nom, ced, fnac, number, num_class, True, 'Faltan campos por rellenar.', 
                False, None, None, None, None, None, False, None]
        else:
            # If the fields are complete, then add to database
            bol, results = fetch_sql(mysql.connector.connect(**keys.config), 
                f'''SELECT * FROM clinica WHERE (APELLIDO = UPPER('{ap}') AND NOMBRE = UPPER('{nom}') ) 
                OR (CEDULA = UPPER('{ced}') AND CEDULA <> '') OR NO = {number};''')
            if bol and results==None: # If the select statement returns None, means theres no similar record
                # Can be added
                try:
                    result1, e = insert_sql(mysql.connector.connect(**keys.config), 'clinica', 
                        APELLIDO=ap.upper(), NOMBRE=nom.upper(), CEDULA=ced.upper(), 
                        FECHA_NAC=fnac, NO=number)
                    if result1:
                        time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        result2, e = insert_sql(mysql.connector.connect(**keys.config), 'movements',
                            ID=e, TRANSACTION='ADD', DATEADDED=time_now, 
                            APELLIDO=ap.upper(), NOMBRE=nom.upper(), CEDULA=ced.upper(), 
                            FECHA_NAC=fnac, NO=number)
                        if not result2: raise e
                    else: raise e
                    ## If the record was added succesfully then the datatable has to be updated (jumps to second block)
                    modified = True
                except Exception as e:
                    logging.exception(f'''[Movements] Error adding record: {ap}, {nom} {ced} - {fnac} - {number}. Exception: {e}''')
                    return [add_data, ap, nom, ced, fnac, number, 'input-style-s', True, f'Error. {e}', 
                        False, None, None, None, None, None, False, None]
            elif bol==False:
                logging.exception(f'''[Clinica] Error fetching records to check add record. Exception: {results}''')
                return [add_data, ap, nom, ced, fnac, number, 'input-style-s', True, f'Error. {results}', 
                    False, None, None, None, None, None, False, None]
            else:
                # Cannot be added because there's already a similar record
                return [add_data, ap, nom, ced, fnac, number, 'input-style-s', True, 
                    'Error. Existe un registro con el mismo número de cédula y/o expediente.', 
                    False, None, None, None, None, None, False, None]
    elif triggered_id=='button-modificar-mod':
        ## Update table for modificar action
        if ( isempty(m_ap) or isempty(m_nom) or isempty(m_ced) or isempty(m_fnac) or isempty(m_num) ):
            # Show modal error
            return [ add_data, ap, nom, ced, fnac, number, 'input-style-s', True,
                'Error. Faltan campos por rellenar.', False, None, None, None, None, None,
                False, None]
        else:
            ## Check if values are already in the database
            bol, results = fetch_sql(mysql.connector.connect(**keys.config),
                f'''SELECT * FROM clinica WHERE ID != {cell['row_id']}
                    AND ( (APELLIDO = UPPER('{m_ap}') AND NOMBRE = UPPER('{m_nom}') ) 
                        OR (CEDULA = UPPER('{m_ced}') AND CEDULA != '') OR NO = '{m_num}');''')
            if bol and results==None:
                ## Can be modified
                modify, e = modify_sql(mysql.connector.connect(**keys.config),
                    'clinica', values={'APELLIDO':m_ap, 'NOMBRE':m_nom, 'CEDULA':m_ced, 
                        'FECHA_NAC':m_fnac, 'NO':m_num}, conditions={'ID':cell['row_id']} )
                modify2, e = modify_sql(mysql.connector.connect(**keys.config),
                    'movements', values={'APELLIDO':m_ap, 'NOMBRE':m_nom, 'CEDULA':m_ced, 
                        'FECHA_NAC':m_fnac, 'NO':m_num}, 
                    conditions={'ID':cell['row_id'], 'TRANSACTION':'ADD'} )
                if modify: 
                    modified = True ## Record modified
                    if modify2: logging.info(f'''[Movements] Record {cell['row_id']} succesfully modified.''')
                    else: logging.error(f'''[Movements] Error updating record {cell['row_id']}.''')
                    data = pd.DataFrame(add_data, columns=['id', 'apellido', 'nombre', 
                            'cedula', 'fecha_nac', 'number'])
                    row = data[data.id==cell['row_id']].squeeze()
                    ## Adding insert query with modified into movements
                    time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    modify_mov, modify_e = insert_sql(mysql.connector.connect(**keys.config), 'movements',
                            ID=cell['row_id'], TRANSACTION='MODIFY', DATEADDED=time_now, 
                            APELLIDO=row.apellido.upper(), NOMBRE=row.nombre.upper(), 
                            CEDULA=row.cedula.upper(), FECHA_NAC=row.fecha_nac, NO=row.number)
                    if modify_mov: 
                        logging.info(f'''[Clinica] Record {cell['row_id']} succesfully modified.''')
                    else: 
                        logging.exception(f'''[Movements] Error adding record {cell['row_id']}. Exception: {modify_e}''')
                    # In this step, the condition doesnt return thus jumps to search condition
                else: 
                    logging.exception(f'''[Clinica] Error modifying record {cell['row_id']}.\nException: {e}''')
                    
                    return [ add_data, ap, nom, ced, fnac, number, 'input-style-s', True,
                        f'Error modificando el registro.', 
                        False, None, None, None, None, None, False, None]
            else: 
                return [ add_data, ap, nom, ced, fnac, number, 'input-style-s', True,
                    f'Error. Ya existe un registro similar: \n{results}.', 
                    False, None, None, None, None, None, False, None]
    elif triggered_id=='msg-eliminar2':
        data = pd.DataFrame(add_data, columns=['id', 'apellido', 'nombre', 
                'cedula', 'fecha_nac', 'number'])
        row = data[data.id==cell['row_id']].squeeze()
        time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        add_del_mov, add_del_e = insert_sql(mysql.connector.connect(**keys.config), 'movements',
                        ID=cell['row_id'], TRANSACTION='DELETE', DATEADDED=time_now, 
                        APELLIDO=row.apellido.upper(), NOMBRE=row.nombre.upper(), 
                        CEDULA=row.cedula.upper(), FECHA_NAC=row.fecha_nac, NO=row.number)
        if add_del_mov: 
            logging.info(f'''[Movements] Record {cell['row_id']} succesfully added.''')
            # Delete from tables
            delete_mov, delete_e = delete_sql(mysql.connector.connect(**keys.config), 'clinica', cell['row_id'])
            delete_mov2, delete_e2 = delete_sql(mysql.connector.connect(**keys.config), 
                                        'movements', cell['row_id'], transaction=True)
            if delete_mov: 
                modified = True
                logging.info(f'''[Clinica] Record {cell['row_id']} succesfully deleted.''')
            else: 
                logging.exception(f'''[Clinica] Error deleting record {cell['row_id']}. Exception: {delete_e}''')
                return [ add_data, ap, nom, ced, fnac, number, 'input-style-s', True,
                    f'Error eliminando el registro.', 
                    False, None, None, None, None, None, False, None]
            if not delete_mov2: 
                logging.exception(f'''[Movements] Error deleting record {cell['row_id']}. Exception: {delete_e2}''')
        else: logging.exception(f'''[Movements] Error adding record [{row}].\nException: {add_del_e}''')
    
    ### Second block of conditions
    if modified or (triggered_id=='tabs-main' and tab=='agregar'):
        bol, results = fetch_sql(mysql.connector.connect(**keys.config), fetch=2,
            query=f'''SELECT * FROM movements WHERE No>{config['last_num']} AND TRANSACTION='ADD';''')
        if bol:
            final_results = pd.DataFrame(results, columns=['id', 'transaction', 'dateadded', 
                'apellido', 'nombre', 'cedula', 'fecha_nac', 'direccion', 'number'])
            return [final_results.sort_values(by='id', ascending=False).to_dict('records'), '', '', 
                None, None, None, 'input-style-s', False, message,
                False, None, None, None, None, None, False, None]
        elif bol==False:
            logging.exception(f'''Error getting last added records. Last number: {config['last_num']}. Exception: {results}''')
            return [add_data, ap, nom, ced, fnac, number, 'input-style-s', True, f'Error: {results}', 
                False, None, None, None, None, None, False, None]
    elif triggered_id=='button-limpiar2':
        bol, results = fetch_sql(mysql.connector.connect(**keys.config),
            f'''SELECT MAX(No) FROM movements WHERE TRANSACTION='ADD';''')
        if bol:
            # Create dictionary variable with max number
            config = {'last_num':results[0]}
            # Dump json of dictionary into config file
            json.dump(config, open(config_file, 'w'))
            logging.info(f'''Tab Add. Resetting last ID: {results[0]}.''')
        elif bol==False:
            logging.exception(f'''Error getting max ID. Last number: {config['last_num']}. Exception: {results}''')
        return [None, '', '', None, None, None, 'input-style-s', False, message, 
            False, None, None, None, None, None, False, None]
    elif triggered_id=='button-modificar2' or triggered_id=='button-restaurar-mod':
        if cell!=None and len(add_data)>0:
            data = pd.DataFrame(add_data, columns=['id', 'apellido', 'nombre', 
                            'cedula', 'fecha_nac', 'number'])
            row = data[data.id==cell['row_id']].squeeze()
            # modal open return value depending on callback trigger
            open_value = m_open if triggered_id=='button-restaurar-mod' else not m_open
            # Shows the information from the selected row into the modal
            return [ add_data, ap, nom, ced, fnac, number, 'input-style-s', False, '',  
                open_value, row.number, row.apellido, row.nombre, row.cedula, row.fecha_nac, False, '']
    elif triggered_id=='button-eliminar2' and cell!=None and len(add_data)>0:
        # Button from main tab that shows a message box (msg-eliminar)
        data = pd.DataFrame(add_data, columns=['id', 'apellido', 'nombre', 
                'cedula', 'fecha_nac', 'number'])
        if cell['row_id'] in data.id.values:
            row = data[data.id==cell['row_id']].squeeze()
            return [add_data, ap, nom, ced, fnac, number, 'input-style-s', False, '', 
                False, None, None, None, None, None, True, 
                f'Seguro desea eliminar el siguiente registro?\nNombre: {row.apellido}, {row.nombre}\nExpediente: {row.number}']
        else: return [add_data, ap, nom, ced, fnac, number, 'input-style-s', True, 
            f'Error. Por favor vuelva a seleccionar otra casilla del mismo registro e intente nuevamente.', 
            False, None, None, None, None, None, False, None]
    elif triggered_id=='check-id-button' and check_click!=None:
        ### Check number id button if already exists
        bol, results = fetch_sql(mysql.connector.connect(**keys.config),
            f'SELECT NO FROM clinica WHERE NO={number}')
        if bol:
            return [add_data, ap, nom, ced, fnac, number, 
                f'input-style-s {"input-green" if results==None else "input-red"}', 
                False, message, False, None, None, None, None, None, False, None]
        elif bol==False:
            logging.exception(f'''[Clinica] Error fetching record {number}. Exception: {results}''')
            return [add_data, ap, nom, ced, fnac, number, 'input-style-s', True, f'Error.', 
                False, None, None, None, None, None, False, None]
    elif triggered_id=='set-id-button' and set_click!=None:
        ### Set id button generates a new number by adding 1 to the max number
        bol, results = fetch_sql(mysql.connector.connect(**keys.config), 
                    f'SELECT MAX(NO) FROM clinica')
        if bol and results==None:
            return [add_data, ap, nom, ced, fnac, '', 'input-style-s', False, message, 
                False, None, None, None, None, None, False, None]
        elif bol==False:
            logging.exception(f'''[Clinica] Error fetching max record. Exception: {results}''')
            return [add_data, ap, nom, ced, fnac, '', 'input-style-s', True, f'Error.', 
                False, None, None, None, None, None, False, None]
        else:
            return [add_data, ap, nom, ced, fnac, results[0]+1, 'input-style-s', False, message, 
                False, None, None, None, None, None, False, None]
    return [add_data, ap, nom, ced, fnac, number, 'input-style-s', False, message, 
                False, None, None, None, None, None, False, None]


