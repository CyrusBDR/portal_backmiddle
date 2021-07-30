import dash
from flask import Flask, send_from_directory
from herokk.x_infinity.config_auth import config_auth
from herokk.x_infinity.users_mgt import db, User as base
from flask_login import LoginManager, UserMixin
import os
import dash_bootstrap_components as dbc


external_stylesheets=[dbc.themes.BOOTSTRAP]
VALID_USERNAME_PASSWORD_PAIRS = [('BDR', '12345678')]

server = Flask(__name__)
app= dash.Dash(
    __name__, server=server, meta_tags=[{'name': 'viewport', 'content': 'width=device-width'}],external_stylesheets=external_stylesheets
)

# auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

app.config['suppress_callback_exceptions'] = True
# config
server.config.update(
    SECRET_KEY=os.urandom(12),
    SQLALCHEMY_DATABASE_URI=config_auth.get('database', 'con'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)
# server = app.server
db.init_app(server)

# Setup the LoginManager for the server
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'


# Create User class with UserMixin
class User(UserMixin, base):
    pass


# callback to reload the user object
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

