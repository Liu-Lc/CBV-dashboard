#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sunday, July 6, 2021, 08:32
@author: Lucia Liu (lucia.liu@utp.ac.pa)
"""


from dash import dcc, html, dash_table as table, callback_context as ctx
import dash_bootstrap_components as dbc
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
        return True, None
    except Exception as e:
        return False, e
    finally:
        conn.commit()
        cursor.close()
        conn.close()

## Title and Links for styles and fonts
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
                        dcc.DatePickerSingle(id='f-fechanac', className='input-style',
                            clearable=True, display_format='DD/MM/YYYY'),
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
    dbc.Modal([
        dbc.ModalHeader(children=[
            dbc.ModalTitle("Modificar Registro")
        ], close_button=False),
        dbc.ModalBody(children=[
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
                dcc.DatePickerSingle(className='input-style-m',id='modal-fechanac', 
                    clearable=True, display_format='DD/MM/YYYY'),
            ]),
        ]),
        dbc.ModalFooter(
            dbc.Button('Close', id='modificar-close', className='ml-auto')
        ), 
    ],
    id="modal", # Give the modal an id name 
    is_open=False,  # Open the modal at opening the webpage.
    size="lg",  # "sm", "lg", "xl" = small, large or extra large
    backdrop=True,  # Modal to not be closed by clicking on backdrop
    scrollable=True,  # Scrollable in case of large amount of text
    centered=True,  # Vertically center modal 
    fade=True,  # True, False
    )
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
                                    html.I(className='fa fa-asterisk fa-s'),
                                    # tooltip
                                    html.Span(className='tooltip', children=['Generar #']),
                                ]),
                                html.Button(id='check-id-button', className='small-button', children=[
                                    html.I(className='fa fa-check-circle fa-s'),
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
                            dcc.DatePickerSingle(id='a-fechanac', className='input-style',
                                clearable=True, display_format='DD/MM/YYYY'),
                        ]),
                        html.P('', className='spacer'),
                    ]),
                    ## Data Table for results
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
                ## Buttons section at lower side
                html.Div(className='button-container', children=[
                    html.Button('AGREGAR', id='button-agregar', className='large-button'),
                    html.Button('LIMPIAR', id='button-limpiar2', className='large-button'),
                    html.Button('MODIFICAR', id='button-modificar2', className='large-button'),
                    html.Button('ELIMINAR', id='button-eliminar2', className='large-button'),
                ]),
            ])

## Adding a tab container to switch between the searching form and adding form
tabs =  dcc.Tabs(
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
                    children=[form, form_modal] ## Form variable
                ),
                dcc.Tab(
                    label='Agregar',
                    value='agregar',
                    className='tab',
                    selected_className='tab-selected',
                    children=[form_add] ## Add form variable
                ),
            ]
        )


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
def button_buscar_click(search_click, clean_click, search_option, ap1, ap2, nom, ced, fnac):
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
            return pd.DataFrame(results, 
                    columns=['id', 'apellido', 'nombre', 
                        'cedula', 'fecha_nac', 'number']).to_dict('records'), ap1, ap2, nom, ced, fnac
        else: return [], ap1, ap2, nom, ced, fnac

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
        if ap==None or ap=='' or nom==None or nom=='' or ced==None or ced=='' or fnac==None or number==None or number=='':
            # Returns True to displayed message for empty fields
            return data, ap, nom, ced, fnac, number, num_class, True, 'Faltan campos por rellenar.'
        else:
            # If the fields are complete, then add to database
            try:
                results = fetch_sql(mysql.connector.connect(**keys.config), 
                        f'''SELECT * FROM clinica WHERE (APELLIDO = '{ap}' AND NOMBRE = '{nom}') 
                        OR (CEDULA = '{ced}' AND CEDULA != '') OR NO = '{number}';''')
            except:
                return data, ap, nom, ced, fnac, number, num_class, True, 'Error: No connection.'
            if results==None: # If the select statement returns None, means theres no similar record
                # Can be added
                # insert_query = f'''INSERT INTO %s (APELLIDO, NOMBRE, CEDULA, FECHA_NAC, NO) VALUES('{ap}', '{nom}', '{ced}', '{fnac}', {number});'''
                try:
                    values = f''' '{ap}', '{nom}', '{ced}', '{fnac}', {number}'''
                    result1, e = insert_sql(mysql.connector.connect(**keys.config),
                        'clinica', values=values)
                    result2, e = insert_sql(mysql.connector.connect(**keys.config),
                        columns=''' TRANSACTION, APELLIDO, NOMBRE, CEDULA, FECHA_NAC, NO ''' 
                        'movements', values=''' 'ADD',''' + values)
                    if result1 and result2:
                        results = (None, '', '', '', 'Null', '', num_class, False, '')
                    else: raise e
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
                results = (data, '', '', '', 'Null', '', num_class, False, '')
            except Exception as e:
                print(f'Error updating data table. {e}')
                return (data, ap, nom, ced, fnac, number, num_class, True, 'Error has ocurred.')
            print(results)
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
                query=f'''SELECT * FROM added WHERE No>{config['last_num']};''')
            return [pd.DataFrame(results, columns=['id', 'apellido', 'nombre', 
                'cedula', 'fecha_nac', 'direccion', 'number']).to_dict('records'), 
                None, None, None, None, None, num_class, False, message]
    return data, ap, nom, ced, fnac, number, num_class, False, message

@app.callback(
    Output('modal', 'is_open'),
    [Input('button-modificar1', 'n_clicks'), Input('modificar-close', 'n_clicks')],
    [State('modal', 'is_open')]
)
def toggle_modal(open, close, is_open):
    if open or close:
        return not is_open
    return is_open

