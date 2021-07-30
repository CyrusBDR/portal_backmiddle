# Dash configuration
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from herokk.x_infinity.page_lamina_xinfinity import app
import dash_bootstrap_components as dbc

# Create app layout
layout =html.Div([ html.Div(children=[
    dcc.Location(id='url_logout', refresh=True),
    html.Div(
        className="container",
        children=[
            html.Div(
                html.Div(
                    className="row",
                    children=[
                        html.Div(

                            children=[
                                html.Br(),
                                html.Div('User disconnected - Please login to view the success screen again'),
                            ]
                        ),
                        html.Div(

                            # children=html.A(html.Button('LogOut'), href='/')
                            children=[

                                dbc.Button(id='back-button', children='Go back', n_clicks=0,className="ml-2",style={'margin-left':'50%','margin-top':'15%'})
                            ]
                        )
                    ]
                )
            )
        ]
    )
],style={'width':'50%','margin-left':'25%','border': '4px','border-radius': '12px','background-color':'white','margin-top':'15%','padding': '20px','float':'left'}
)],style={'background-image':'linear-gradient(to bottom, transparent 0%, #F5F5F5 90%),url(https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHkaGbVUAP73VwnxmNUAthk1A5X0T89JTRAw&usqp=CAU)','background-size': 'cover','height':'100vh'})


# Create callbacks
@app.callback(Output('url_logout', 'pathname'),
              [Input('back-button', 'n_clicks')])
def logout_dashboard(n_clicks):
    if n_clicks > 0:
        return '/'
