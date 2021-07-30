import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from flask_login import login_user
from werkzeug.security import check_password_hash
import visdcc
import dash_bootstrap_components as dbc
from flask_login import LoginManager, UserMixin, current_user
from herokk.x_infinity.users_mgt import *
from herokk.x_infinity.page_lamina_xinfinity import app
layout =html.Div([ dbc.Row([
            dbc.Col([
                html.Img(src=app.get_asset_url("bdrlogotransparente.png"), height="118px", width='auto',
                         style={'margin-left': '1.5%', 'margin-top': '7%'})],width={"size": 2, "order": 1, "offset": 3}),
            dbc.Col([
                html.Title('Portal Cedentes',
                       style={'margin-left': '0px', 'padding-top': '11%', 'font-weight': '550',
                              'font-size': '20px'})],width={"size":4, "order": 3, "offset": -2}), ],no_gutters=True,style={ 'display': 'flex',
  'flex-direction': 'row','width':'100%','height':'120px'} ),
    html.Div([html.Div( children=[
                visdcc.Run_js(id='javascript_logout'),
                dcc.Location(id='url_login', refresh=True),html.Div([html.Div('Portal Cedentes - ',className='three Columns',style={'font-weight':'500','margin-left':'2%'}),
                html.Div(''' Change Password:''', id='h1',className='three columns',style={'margin-left':'2%'})],className='row'),html.Br(),
                html.Div(
                    # method='Post',
                    children=[

                        dbc.Input(
                            placeholder='Enter your new password',
                            n_submit=0,
                            type='password',
                            id='lala-box'
                        ),html.Br(), dbc.FormGroup(
            [

                dbc.Input(id='lala-box1',type='password',placeholder='Confirm your new password'),

                dbc.FormFeedback("As senhas correspondem",
                    valid=True
                ),
                dbc.FormFeedback(
                    "As senhas não correspondem",
                    valid=False,
                ),
            ]
        ), html.Br(),
                        dbc.Button(
                            children='Submit',
                            n_clicks=0,
                            id='submit-np'
                        ), dbc.Button("Voltar",color='Link',href='/'),
                        html.Div(children='', id='output-np'),dbc.Modal(
            [
                dbc.ModalHeader("Senha alterada com sucesso"),
                dbc.ModalBody([html.Div([html.P("Faça o login novamente para prosseguir")]),
                                        ]),
                dbc.ModalFooter(
                    dbc.Button(children=['Login'],  href='/login')
                ),
            ],
            id="modal-cp",
            centered=True,
            is_open=False,
        ),
                    ]
                ),
            ]
        )],style={'width':'50%','margin-left':'25%','border': '4px','border-radius': '12px','background-color':'white','margin-top':'0.5%','padding': '20px','float':'left'}
)],style={'background-image':'linear-gradient(to bottom, transparent 0%, #F5F5F5 90%),url(https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHkaGbVUAP73VwnxmNUAthk1A5X0T89JTRAw&usqp=CAU)','background-size': 'cover','height':'100vh'})



@app.callback(
    Output("modal-cp", "is_open"),
    [Input('submit-np', "n_clicks")],Input('lala-box','value'),
    [State("modal-cp", "is_open")],
)
def toggle_modal(n1,passw, is_open):
    try:
        if n1%2!=0:
            name=current_user.username
            email='renata.bs@uol.com.br'
            del_user(name)
            add_user(name, passw, email)

            return not is_open
        return is_open
    except:
        pass


@app.callback([Output('lala-box1','valid'), Output('lala-box1', "invalid")],[Input('lala-box','value'),Input('lala-box1','value')],)
def check_validity(l1,l2):
    if l2:
        is_gmail = l2==l1
        return is_gmail, not is_gmail
    return False, False