from flask import Flask, render_template
import pandas as pd
import json
import plotly
import ast
import plotly.express as px
from flask import url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/sentiment')
def sentiment():
    return render_template('sentiment.html')

@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0")
