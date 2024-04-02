from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson import ObjectId
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
    # Fetch all cities for the dropdown
    cities = locations_collection.distinct("city")

    # Fetch all owners for the dropdown
    owners = list(owners_collection.find({}, {"_id": 1, "first_name": 1, "last_name": 1}))

    # Retrieve query parameters
    selected_city = request.args.get('city')
    owner_id = request.args.get('owner_id')
    multiple_sales_filter = request.args.get('multiple_sales') == '1'

    # Construct the query
    query = {}
    if selected_city:
        query["location.city"] = selected_city
    if owner_id:
        query["owner._id"] = ObjectId(owner_id)

    if multiple_sales_filter:
        pipeline = [
            {"$group": {
                "_id": "$home",
                "count": {"$sum": 1}
            }},
            {"$match": {
                "count": {"$gt": 1}
            }}
        ]
        multiple_sales = transactions_collection.aggregate(pipeline)
        home_ids = [sale['_id'] for sale in multiple_sales]
        query["_id"] = {"$in": home_ids}

    # Retrieve the filtered list of homes based on the query
    homes = list(homes_collection.find(query))

    return render_template('list_homes.html', homes=homes, cities=cities, owners=owners)

# Adding a home form - make sure this is the approach we should be using
@app.route('/add_home', methods=['GET', 'POST'])
def add_home():
    # Query the database for appliances before rendering the form
    appliances = list(appliances_collection.find())
    owners = list(owners_collection.find())

    insert = True # start as true until some check fails
    if request.method == 'POST':
        try:
            print(request.form)
            # todo: fix this to actually validate the user input was good otherwise
            floor_space = int(request.form.get('floor_space', 0))
            floors = int(request.form.get('floors', 0))
            bed_rooms = int(request.form.get('bed_rooms', 0))
            bath_rooms = float(request.form.get('bath_rooms', 0.0))  # Assuming bathrooms can be fractions
            # land size needs rework to acres to sq ft
            land_size = float(request.form.get('land_size', 0.0))
            year_constructed = int(request.form.get('year_constructed', 0))
            for_sale = request.form.get('for_sale') == 'True'
            
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

            # Extract the list of selected appliance IDs from the form
            selected_appliance_ids = request.form.getlist('appliances')
            # Fetch the full documents for the selected appliances
            selected_appliances = list(appliances_collection.find({"_id": {"$in": [ObjectId(id) for id in selected_appliance_ids]}}))
            
            owner_id = request.form.get('owner')
            # Find the complete owner document including its _id
            owner_document = owners_collection.find_one({"_id": ObjectId(owner_id)})

            # GET LOCATION DATA IN HERE
            # Extract location information from the form
            location_info = {
                'street_number': request.form.get('street_number'),
                'unit_number': request.form.get('unit_number', ''),
                'street': request.form.get('street'),
                'city': request.form.get('city'),
                'zip': request.form.get('zip'),
                'state': request.form.get('state'),
                'county': request.form.get('county'),
                'country': request.form.get('country'),
            }
            # Insert the location into the locations collection and get the inserted ID
            inserted_location = locations_collection.insert_one(location_info).inserted_id
            # Now retrieve the full document with the generated _id to embed
            location_document = locations_collection.find_one({"_id": inserted_location})

            home_data = {
                db.HOME.floor_space: floor_space,
                db.HOME.floors: floors,
                db.HOME.bed_rooms: bed_rooms,
                db.HOME.bath_rooms: bath_rooms,
                db.HOME.land_size: land_size,
                db.HOME.year_constructed: year_constructed,
                db.HOME.home_type: home_type_user_input,
                db.HOME.appliances: selected_appliances,
                db.HOME.owner: owner_document,
                db.HOME.location: location_document
            }
            
            if insert == True:
                homes_collection.insert_one(home_data)
                flash('Home added successfully!', 'success')  # Flash a success message
            else:
                flash('Home not inserted...', 'fail')  # Flash a success message
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')  # Flash an error message
        return redirect(url_for('add_home'))
    return render_template('add_home.html', appliances = appliances, owners = owners)

@app.route('/add_owner', methods=['GET'])
def add_owner_form():
    return render_template('add_owner.html')

@app.route('/add_owner', methods=['POST'])
def add_owner():
    try:
        owner_data = {
            "first_name": request.form['first_name'],
            "last_name": request.form['last_name'],
            "ssn": request.form['ssn'],
            "no_dependents": int(request.form['no_dependents']),
            "income": float(request.form['income']),
            "age": int(request.form['age']),
            "profession": request.form['profession'],
        }
        owners_collection.insert_one(owner_data)
        flash('Owner added successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
    return redirect(url_for('add_owner_form'))


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
    return render_template('add_agent.html', companies=companies)
   
@app.route('/transactions')
def transactions():
    # Fetch all transactions and the related home details
    all_transactions = transactions_collection.find().sort('date', -1)  # Newest transactions first
    transactions_details = []

    for trans in all_transactions:
        # Fetch each home by its ID stored in the transaction
        home = homes_collection.find_one({"_id": trans['home']})
        agent = agents_collection.find_one({"_id": trans['agent']})
        company = companies_collection.find_one({"_id": trans['company']})
        owner = owners_collection.find_one({"_id": trans['seller']})
        buyer = owners_collection.find_one({"_id": trans['buyer']})
        
        # Check if the home document was found
        if home:
            # Extract the location subdocument
            location = home.get('location', {})
            # Prepare a full address string using the location details
            full_address = f"{location.get('street_number', '')} {location.get('street', '')}, " \
                           f"{location.get('city', '')}, {location.get('state', '')} " \
                           f"{location.get('zip', '')}"
            # Combine transaction, home, and location details
            transaction_data = {
                "date": trans["date"],
                "price": trans["price"],
                "buyer_details":  buyer,
                "home_details": home,
                "owner_details": owner,
                "agent_details": agent if agent else "Agent details not found",
                "company_details": company if company else "Company details not found",
                "full_address": full_address  # Add the full address to the transaction data
            }

            # print(owner)
            transactions_details.append(transaction_data)
        else:
            transactions_details.append({"date": trans["date"], "price": trans["price"], "home_details": "Home not found"})
    
    return render_template('transactions.html', transactions=transactions_details)