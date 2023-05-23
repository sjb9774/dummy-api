from flask import Flask

app = Flask(__name__)

from dummy_api.api import *