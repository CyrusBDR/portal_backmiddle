# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
from flask import Flask
import plotly.graph_objs as go

###################### inputs #####################
fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[4, 1, 2])])
grafico = dcc.Graph(id='example-graph-2',figure=fig)



###################### NAVBAR #####################
#icone = 'https://cdn.onlinewebfonts.com/svg/img_130996.png'

search_bar = dbc.Row([
                dbc.Col(dbc.Button("Config", outline=True, color="light", className="mr-1")),
                ],
                no_gutters=True,
                className="ml-auto flex-nowrap mt-3 mt-md-0",
                align="center",
                )
navbar = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [dbc.Col(dbc.NavbarBrand("BDR app", className="ml-2")),
                ],
                align="center",
                no_gutters=True,
            ),
            href="https://plotly.com",
        ),
        dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
        dbc.Collapse(
            search_bar, id="navbar-collapse", navbar=True, is_open=False
        ),
    ],
    color="dark",
    dark=True,
                    )

###################### TAB 1 #####################

tab_1 = html.Div(
        dbc.CardBody([
        #bloco 1
                dbc.Row([
                    dbc.Col([html.P('Rent. Mês' ,style={'font-size':'75%'})
                            ]),
                        ]),
                dbc.Row([
                    dbc.Col([html.H5('0,25%', className='card-title'), html.Hr(),
                            ]),
                        ]),

        #grafico 1
                    dbc.Row([
                    dbc.Col(grafico, width=6),
                    ]),
            ]),
        )

##################
#bloco retorno nav pricipal


#body_1_app =

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
        })

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")



######################## FOOTER #################################
footer = dbc.CardFooter("© Copyright 2019 - BDR Investimentos Ltda - Todos os direitos reservados - "
               "Esta página é um material gerencial para organizar a agenda de atividades dos Prestadores de Serviços do FIP Madagascar")











######################### definicao tema página ###########
external_stylesheets=[dbc.themes.BOOTSTRAP]
server = Flask(__name__)
app= dash.Dash(
    __name__, server=server, meta_tags=[{'name': 'viewport', 'content': 'width=device-width'}],external_stylesheets=external_stylesheets)

app.layout = html.Div([
                navbar,
                tab_1,
                footer

                ])






if __name__ == '__main__':
    app.run_server(debug=True)