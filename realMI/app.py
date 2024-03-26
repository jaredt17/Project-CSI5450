from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import db

from bson import ObjectId

from init_db import init_db


app = Flask(__name__)
app.secret_key = 'your_secret_key'

client = MongoClient()
client.drop_database(db.DB)
database = client['realmi']

# Define collections
homes_collection = database['HOMES']
locations_collection = database["LOCATIONS"]
appliances_collection = database["APPLIANCES"]
agents_collection = database["AGENTS"]
owners_collection = database["OWNERS"]
transactions_collection = database["TRANSACTIONS"]
companies_collection = database["COMPANIES"]

init_db()

# Starting app
@app.route('/', methods=('GET', 'POST'))
def index():
    return render_template('index.html')

# Homes page
@app.route('/homes')
def list_homes():
    homes = list(homes_collection.find())  # Fetch all homes
    return render_template('list_homes.html', homes=homes)

# Adding a home form - make sure this is the approach we should be using
@app.route('/add_home', methods=['GET', 'POST'])
def add_home():
    insert = True # start as true until some check fails
    if request.method == 'POST':
        try:
            # todo: fix this to actually validate the user input was good otherwise
            floor_space = int(request.form.get('floor_space', 0))
            floors = int(request.form.get('floors', 0))
            bed_rooms = int(request.form.get('bed_rooms', 0))
            bath_rooms = float(request.form.get('bath_rooms', 0.0))  # Assuming bathrooms can be fractions
            # land size needs rework to acres to sq ft
            land_size = int(request.form.get('land_size', 0))
            year_constructed = int(request.form.get('year_constructed', 0))
            
            # compare this to validate
            home_type_user_input = request.form.get('home_type')
            
            # call our hometype function to decide what style of home this is, the user should not be allowed to set incorrectly
            home_type_valid = db.HomeType.validate(home_type_user_input, floor_space, floors, bed_rooms, land_size)

            print(home_type_valid) # debug

            if home_type_valid == False:
                flash(f'Home type not valid for the entered paramaters.')  # Flash an error message
                insert = False
            else:
                print("Home Passed validation") 
            
            home_data = {
                db.HOME.floor_space: floor_space,
                db.HOME.floors: floors,
                db.HOME.bed_rooms: bed_rooms,
                db.HOME.bath_rooms: bath_rooms,
                db.HOME.land_size: land_size,
                db.HOME.year_constructed: year_constructed,
                db.HOME.home_type: home_type_user_input,
            }
            
            if insert == True:
                homes_collection.insert_one(home_data)
                flash('Home added successfully!', 'success')  # Flash a success message
            else:
                flash('Home not inserted...', 'fail')  # Flash a success message
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')  # Flash an error message
        return redirect(url_for('add_home'))
    return render_template('add_home.html')


@app.route('/add_agent', methods=['GET', 'POST'])
def add_agent():
    companies = list(companies_collection.find())
    insert = True
    if request.method == 'POST':
        try:
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')

            companies_ids = request.form.getlist('companies')
            selected_companies = list(companies_collection.find({"_id": {"$in": [ObjectId(id) for id in companies_ids]}}))

            agent_data = {
                db.AGENT.first_name: first_name,
                db.AGENT.last_name: last_name,
                db.AGENT.companies: selected_companies
            }

            if insert == True:
                agents_collection.insert_one(agent_data)
                flash('Agent added successfully!', 'success')
            else:
                flash('Agent not inserted...', 'fail')
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')  # Flash an error message
        return redirect(url_for('add_agent'))
    return render_template('add_agent_html', companies=companies)
    