from flask import Flask, render_template, request, url_for, redirect
from pymongo import MongoClient


app = Flask(__name__)

client = MongoClient()

db = client.flask_db

# Starting app
@app.route('/', methods=('GET', 'POST'))
def index():
    return render_template('index.html')