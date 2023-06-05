from flask import Flask

app = Flask(__name__)
name = "looking_glass"

import looking_glass.app
