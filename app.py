from flask import Flask

app = Flask(__name__)

COUNT_TEST = 0

from .api import *
