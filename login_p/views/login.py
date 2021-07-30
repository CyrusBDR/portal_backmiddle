import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from email.message import EmailMessage
import smtplib
from herokk.x_infinity.users_mgt import *
import email as emaillib
from email import *
from flask_login import login_user
from werkzeug.security import check_password_hash
import visdcc
import dash_bootstrap_components as dbc
from herokk.x_infinity.page_lamina_xinfinity import app
layout =html.Div([ dcc.Location(id='url_login', refresh=True),dbc.Row([
            dbc.Col([
                html.Img(src=app.get_asset_url("bdrlogotransparente.png"), height="118px", width='auto',
                         style={'margin-left': '1.5%', 'margin-top': '7%'})],width={"size": 2, "order": 1, "offset": 3}),
            dbc.Col([
                html.Title('Portal Cedentes',
                       style={'margin-left': '0px', 'padding-top': '11%', 'font-weight': '550',
                              'font-size': '20px'})],width={"size":4, "order": 3, "offset": -2}), ],no_gutters=True,style={ 'display': 'flex',
  'flex-direction': 'row','width':'100%','height':'120px'} ),
    html.Div([html.Div(children=[
                visdcc.Run_js(id='javascript_logout'),
                dcc.Location(id='url_login', refresh=True),html.Div([html.Div('Portal Cedentes - ',className='three Columns',style={'font-weight':'500','margin-left':'2%'}),
                html.Div(''' Please log in to continue:''', id='h1',className='three columns',style={'margin-left':'2%'})],className='row'),html.Br(),
                html.Div(
                    # method='Post',
                    children=[
                        dbc.Input(
                            placeholder='Enter your username',
                            n_submit=0,
                            type='text',
                            id='uname-box'
                        ), html.Br(),
                        dbc.Input(
                            placeholder='Enter your password',
                            n_submit=0,
                            type='password',
                            id='pwd-box'
                        ), dbc.Button("Esqueceu sua senha? Clique para recuperar", color="link",id='rec-senha',size='sm'),html.Br(),
                      html.Br(),  dbc.Button(
                            children='Login',
                            n_clicks=0,
                            id='login-button',href='/'
                        ),html.Div(children='', id='output-state'), html.Div(id='outrs'),html.Div(id='outrs1'),

                    ]
                ),
            ]
        )],style={'width':'50%','margin-left':'25%','border': '4px','border-radius': '12px','background-color':'white','margin-top':'0.5%','padding': '20px','float':'left'}
)],style={'background-image':'linear-gradient(to bottom, transparent 0%, #F5F5F5 90%),url(https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHkaGbVUAP73VwnxmNUAthk1A5X0T89JTRAw&usqp=CAU)','background-size': 'cover','height':'100vh'})


@app.callback(Output('outrs','children'),Input('rec-senha','n_clicks'))
def recsenha(n):
    try:
        if n%2!=0:
            return html.Div([html.Br(),html.P('Uma nova senha será enviada para o seu e-mail:'),dbc.FormGroup([dbc.Input(placeholder='Enter your e-mail',id='entraem'), dbc.FormFeedback(valid=True ),
                dbc.FormFeedback( valid=False)]),html.Br(),dbc.Button('Enviar e-mail', id='enviaremrs')])
        return ''
    except:
        pass

@app.callback(Output('outrs1','children'),Input('enviaremrs','n_clicks'),Input('entraem','value'))
def email(nn,emee):
    try:
        if nn%2!=0:
            del_user('test')
            add_user('test','Cedente123','la@bdrasset.com.br')
            msg = emaillib.message_from_string('Sua senha foi reconfigurada: Cedente123 \n\n Faca seu login novamente no portal.\n\n Recomendamos que troque sua senha: User - Trocar senha.\n\n Acesse: http://uploadfilebdr.herokuapp.com/')
            msg['From'] = "luizaa_arouca@hotmail.com"
            msg['To'] = emee
            msg['Subject'] = "Recuperar Senha - Portal Cedentes BDR"
            s = smtplib.SMTP("smtp.live.com", 587)
            s.ehlo()  # Hostname to send for this command defaults to the fully qualified domain name of the local host.
            s.starttls()  # Puts connection to SMTP server in TLS mode
            s.ehlo()
            s.login('luizaa_arouca@hotmail.com', 'Antonio2013')
            s.sendmail('luizaa_arouca@hotmail.com', emee, msg.as_string())
            s.quit()
            return html.Div([html.Br(),html.P('email enviado')])
        return ''
    except:
        pass



@app.callback([Output('entraem','valid'), Output('entraem', "invalid")],[Input('entraem','value')],)
def check_validity(kl):
    if kl:
        is_gmail = '@' in kl and "." in kl
        return is_gmail, not is_gmail
    return False, False