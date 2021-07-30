import configparser
from sqlalchemy import create_engine

config_auth = configparser.ConfigParser()
config_auth.read('config.txt')

engine = create_engine(config_auth.get('database', 'con'))
