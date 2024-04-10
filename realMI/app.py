from datetime import datetime
from typing import Any, List, Tuple
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson import ObjectId, json_util
import db
from queries import Queries
import json


app = Flask(__name__)
app.secret_key = "your_secret_key"

client = MongoClient()
client.drop_database(db.DB)
database = client[db.DB]

with open("db_export.json", "r") as dbw:
    in_db = json.load(dbw)

ac_db: dict = json_util.loads(in_db)

for k in ac_db.keys():
    col = database.create_collection(k)
    col.insert_many(ac_db[k])

# Define collections
homes_collection = database["HOMES"]
locations_collection = database["LOCATIONS"]
appliances_collection = database["APPLIANCES"]
agents_collection = database["AGENTS"]
owners_collection = database["OWNERS"]
transactions_collection = database["TRANSACTIONS"]
companies_collection = database["COMPANIES"]

q = Queries(database)


# Starting app
@app.route("/", methods=("GET", "POST"))
def index():
    return render_template("index.html")


# Homes page
@app.route("/homes")
def list_homes():
    # Fetch all cities for the dropdown
    cities = locations_collection.distinct("city")

    # Fetch all owners for the dropdown
    owners = list(
        owners_collection.find({}, {"_id": 1, "first_name": 1, "last_name": 1})
    )

    home_types = homes_collection.distinct("home_type")

    # for the query in project md
    selected_owner_home_types = request.args.getlist("owner_home_types")

    # Retrieve query parameters
    selected_city = request.args.get("city")
    owner_id = request.args.get("owner_id")
    multiple_sales_filter = request.args.get("multiple_sales") == "1"

    selected_home_types = request.args.getlist("home_types")

    # Construct the query
    query = {}

    # If selected owner home types are provided, adjust the query
    if selected_owner_home_types:
        # Aggregation pipeline to match owners with all selected home types
        pipeline = [
            {"$match": query},  # Apply existing filters
            {
                "$group": {
                    "_id": "$owner._id",
                    "home_types": {"$addToSet": "$home_type"},
                    "owner_data": {"$first": "$owner"},
                }
            },
            {"$match": {"home_types": {"$all": selected_owner_home_types}}},
        ]
        owners_with_all_types = list(homes_collection.aggregate(pipeline))
        owner_ids_with_all_types = [owner["_id"] for owner in owners_with_all_types]

        # Adjust the main homes query to include only homes owned by these owners
        if owner_ids_with_all_types:
            query["owner._id"] = {"$in": owner_ids_with_all_types}
        else:
            query["owner._id"] = None  # No owners match the criteria

    if selected_city:
        query["location.city"] = selected_city
    if owner_id:
        query["owner._id"] = ObjectId(owner_id)

    # If selected home types are provided, adjust the query
    if selected_home_types:
        query["home_type"] = {"$in": selected_home_types}

    if multiple_sales_filter:
        pipeline = [
            {"$group": {"_id": "$home", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
        ]
        multiple_sales = transactions_collection.aggregate(pipeline)
        home_ids = [sale["_id"] for sale in multiple_sales]
        query["_id"] = {"$in": home_ids}

    # Retrieve the filtered list of homes based on the query
    homes = list(homes_collection.find(query))

    return render_template(
        "list_homes.html",
        homes=homes,
        cities=cities,
        owners=owners,
        home_types=home_types,
        selected_home_types=selected_home_types,
        selected_owner_home_types=selected_owner_home_types,
    )


# Adding a home form - make sure this is the approach we should be using
@app.route("/add_home", methods=["GET", "POST"])
def add_home():
    # Query the database for appliances before rendering the form
    appliances = list(appliances_collection.find())
    owners = list(owners_collection.find())

    insert = True  # start as true until some check fails
    if request.method == "POST":
        try:
            print(request.form)
            # todo: fix this to actually validate the user input was good otherwise
            floor_space = int(request.form.get("floor_space", 0))
            floors = int(request.form.get("floors", 0))
            bed_rooms = int(request.form.get("bed_rooms", 0))
            bath_rooms = float(
                request.form.get("bath_rooms", 0.0)
            )  # Assuming bathrooms can be fractions
            # land size needs rework to acres to sq ft
            land_size = float(request.form.get("land_size", 0.0))
            year_constructed = int(request.form.get("year_constructed", 0))
            for_sale = request.form.get("for_sale") == "True"

            # compare this to validate
            home_type_user_input = request.form.get("home_type")

            # call our hometype function to decide what style of home this is, the user should not be allowed to set incorrectly
            home_type_valid = db.HomeType.validate(
                home_type_user_input, floor_space, floors, bed_rooms, land_size
            )

            print(home_type_valid)  # debug

            if home_type_valid == False:
                flash(
                    f"Home type not valid for the entered paramaters."
                )  # Flash an error message
                insert = False
            else:
                print("Home Passed validation")

            # Extract the list of selected appliance IDs from the form
            selected_appliance_ids = request.form.getlist("appliances")
            # Fetch the full documents for the selected appliances
            selected_appliances = list(
                appliances_collection.find(
                    {"_id": {"$in": [ObjectId(id) for id in selected_appliance_ids]}}
                )
            )

            owner_id = request.form.get("owner")
            # Find the complete owner document including its _id
            owner_document = owners_collection.find_one({"_id": ObjectId(owner_id)})

            # GET LOCATION DATA IN HERE
            # Extract location information from the form
            location_info = {
                "street_number": request.form.get("street_number"),
                "unit_number": request.form.get("unit_number", ""),
                "street": request.form.get("street"),
                "city": request.form.get("city"),
                "zip": request.form.get("zip"),
                "state": request.form.get("state"),
                "county": request.form.get("county"),
                "country": request.form.get("country"),
            }
            # Insert the location into the locations collection and get the inserted ID
            inserted_location = locations_collection.insert_one(
                location_info
            ).inserted_id
            # Now retrieve the full document with the generated _id to embed
            location_document = locations_collection.find_one(
                {"_id": inserted_location}
            )

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
                db.HOME.location: location_document,
            }

            if insert == True:
                homes_collection.insert_one(home_data)
                flash("Home added successfully!", "success")  # Flash a success message
            else:
                flash("Home not inserted...", "fail")  # Flash a success message
        except Exception as e:
            flash(f"An error occurred: {e}", "error")  # Flash an error message
        return redirect(url_for("add_home"))
    return render_template("add_home.html", appliances=appliances, owners=owners)


# OWNERS PAGE
@app.route("/owners", methods=["POST", "GET"])
def owners():
    if request.method == "POST":
        try:
            owner_data = {
                "first_name": request.form["first_name"],
                "last_name": request.form["last_name"],
                "ssn": request.form["ssn"],
                "no_dependents": int(request.form["no_dependents"]),
                "income": float(request.form["income"]),
                "age": int(request.form["age"]),
                "profession": request.form["profession"],
            }
            owners_collection.insert_one(owner_data)
            flash("Owner added successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
        return redirect(url_for("owners"))

    owners = list(owners_collection.find())

    return render_template("owners.html", owners=owners)


@app.route("/transactions", methods=["POST", "GET"])
def transactions():
    if request.method == "POST":
        try:
            for k in request.values.keys():
                if "sell_" in k:
                    trans_id = k.replace("sell_", "")
                    own_id = ObjectId(request.values.get(k))
                    price = request.values.get(f"price_{trans_id}")
                    if price != "":
                        price = float(price)
                    else:
                        break
                    trans_id = ObjectId(trans_id)

                    transactions_collection.update_one(
                        {"_id": trans_id},
                        {"$set": {"buyer": own_id, "price": price}},
                    )

                    homes_collection.update_one(
                        {
                            "_id": transactions_collection.find_one({"_id": trans_id})[
                                "home"
                            ]
                        },
                        {"$set": {"owner": owners_collection.find({"_id": own_id})}},
                    )
                    flash("Successfully Sold Home", "info")

                elif "update_" in k:
                    trans_id = k.replace("update_", "")
                    agent_id = request.values.get(k, "")
                    price = request.values.get(f"updateprice_{trans_id}")
                    updates = {}

                    try:
                        price = float(price)
                        updates["price"] = price
                    except (ValueError, TypeError):
                        pass

                    if agent_id != "":
                        updates["agent"] = ObjectId(agent_id)

                    trans_id = ObjectId(trans_id)

                    if len(updates) > 0:
                        transactions_collection.update_one(
                            {"_id": trans_id},
                            {"$set": updates},
                        )
                    flash("Successfully Updated Listing", "info")

                elif k == "list":
                    list_home_id = request.values.get("list_home")
                    list_agent_id = request.values.get("list_agent")
                    list_agent_id, list_comp_id = list_agent_id.split("_")
                    list_price = request.values.get("list_price", 0)

                    home_obj = homes_collection.find_one(
                        {"_id": ObjectId(list_home_id)}
                    )
                    agent_obj = agents_collection.find_one(
                        {"_id": ObjectId(list_agent_id)}
                    )
                    comp_obj = companies_collection.find_one(
                        {"_id": ObjectId(list_comp_id)}
                    )

                    new_transaction = {
                        "seller": home_obj["owner"]["_id"],
                        "buyer": None,
                        "home": home_obj["_id"],
                        "agent": agent_obj["_id"],
                        "company": comp_obj["_id"],
                        "date": datetime.now(),
                        "price": float(list_price),
                    }

                    transactions_collection.insert_one(new_transaction)
                    flash("Successfully Listed Home", "info")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")  # Flash an error message
        return redirect(url_for("transactions"))

    owner_id = request.args.get("owner_id")
    sort_order = int(request.args.get("sort_order", -1))
    for_sale = request.args.get("for_sale", "off")

    query = {}
    if owner_id:
        query["seller"] = ObjectId(owner_id)
    if for_sale == "on":
        query["buyer"] = (
            None  # Add condition for homes that are for sale (have no buyer)
        )

    all_transactions = transactions_collection.find(query).sort("price", sort_order)
    transactions_details = []

    for trans in all_transactions:
        home = homes_collection.find_one({"_id": trans["home"]})
        agent = agents_collection.find_one({"_id": trans["agent"]})
        company = companies_collection.find_one({"_id": trans["company"]})
        owner = owners_collection.find_one({"_id": trans["seller"]})
        buyer = owners_collection.find_one(
            {"_id": trans.get("buyer")}
        )  # Use get() to safely handle missing buyer

        if home:
            location = home.get("location", {})
            full_address = (
                f"{location.get('street_number', '')} {location.get('street', '')}, "
                f"{location.get('city', '')}, {location.get('state', '')} "
                f"{location.get('zip', '')}"
            )
            transaction_data = {
                "id": trans["_id"],
                "date": trans["date"],
                "price": trans["price"],
                "buyer_details": buyer,
                "home_details": home,
                "owner_details": owner,
                "agent_details": agent if agent else "Agent details not found",
                "company_details": company if company else "Company details not found",
                "full_address": full_address,
            }
            transactions_details.append(transaction_data)
        else:
            transactions_details.append(
                {
                    "date": trans["date"],
                    "price": trans["price"],
                    "home_details": "Home not found",
                }
            )

    owners = list(
        owners_collection.find({}, {"_id": 1, "first_name": 1, "last_name": 1})
    )
    agents = list(agents_collection.find())
    homes = list(homes_collection.find())
    return render_template(
        "transactions.html",
        transactions=transactions_details,
        owners=owners,
        for_sale=for_sale,
        agents=agents,
        homes=homes,
    )


@app.route("/agents", methods=["GET", "POST"])
def agents():
    companies = list(companies_collection.find())
    agents_list = list(agents_collection.find())

    insert = True
    if request.method == "POST":
        # get the agent ID
        try:
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")

            companies_ids = request.form.getlist("companies")
            selected_companies = list(
                companies_collection.find(
                    {"_id": {"$in": [ObjectId(id) for id in companies_ids]}}
                )
            )

            agent_data = {
                db.AGENT.first_name: first_name,
                db.AGENT.last_name: last_name,
                db.AGENT.companies: selected_companies,
            }

            if insert == True:
                agents_collection.insert_one(agent_data)
                flash("Agent added successfully!", "success")
            else:
                flash("Agent not inserted...", "fail")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")  # Flash an error message
        return redirect(url_for("agents"))

    return render_template("agents.html", companies=companies, agents=agents_list)


@app.route("/companies", methods=["GET", "POST"])
def companies():
    if request.method == "POST":
        try:
            name = request.form.get("name")
            commission = request.form.get("commission")

            new_location = {
                v: request.form.get(v)
                for v in filter(lambda l: "__" not in l, dir(db.LOCATION))
            }
            location = locations_collection.insert_one(new_location)

            company_data = {
                db.COMPANY.name: name,
                db.COMPANY.commission: commission,
                db.COMPANY.location: locations_collection.find_one(
                    {"_id": location.inserted_id}
                ),
            }

            companies_collection.insert_one(company_data)
            flash("Company added successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")  # Flash an error message
        return redirect(url_for("companies"))

    companies = list(companies_collection.find())

    return render_template("companies.html", companies=companies)


@app.route("/locations", methods=["GET"])
def locations():
    locations = list(locations_collection.find())

    return render_template("locations.html", locations=locations)


@app.route("/appliances", methods=["GET", "POST"])
def appliances():
    if request.method == "POST":
        try:
            new_appliance = {
                v: request.form.get(v)
                for v in filter(lambda l: "__" not in l, dir(db.APPLIANCE))
            }
            appliances_collection.insert_one(new_appliance)

            flash("Company added successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")  # Flash an error message
        return redirect(url_for("appliances"))

    appliances = list(appliances_collection.find())

    return render_template("appliances.html", appliances=appliances)


@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        try:
            owner = ObjectId(request.form.get(db.HOME.owner))
            appliance = request.form.getlist("appliances")
            selected_appliances = list(
                appliances_collection.find(
                    {"_id": {"$in": [ObjectId(id) for id in appliance]}}
                )
            )

            new_location = {
                v: request.form.get(v)
                for v in filter(lambda l: "__" not in l, dir(db.LOCATION))
            }
            location = locations_collection.insert_one(new_location)

            new_home = {
                db.HOME.floor_space: request.form.get(db.HOME.floor_space),
                db.HOME.floors: request.form.get(db.HOME.floors),
                db.HOME.bed_rooms: request.form.get(db.HOME.bed_rooms),
                db.HOME.bath_rooms: request.form.get(db.HOME.bath_rooms),
                db.HOME.land_size: request.form.get(db.HOME.land_size),
                db.HOME.year_constructed: request.form.get(db.HOME.year_constructed),
                db.HOME.home_type: request.form.get(db.HOME.home_type),
                db.HOME.appliances: selected_appliances,
                db.HOME.owner: owners_collection.find_one({"_id": owner}),
                db.HOME.location: locations_collection.find_one(
                    {"_id": location.inserted_id}
                ),
            }
            print(new_home)
            homes_collection.insert_one(new_home)

            flash("Home added successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")  # Flash an error message
        return redirect(url_for("home"))

    homes = list(homes_collection.find())
    appliances = list(appliances_collection.find())
    owners = list(owners_collection.find())

    return render_template(
        "home.html", appliances=appliances, homes=homes, owners=owners
    )


class Input:
    SELECT = "select"
    TEXT = "text"
    NUMBER = "number"

    def __init__(self, type, label, id) -> None:
        self.id = id
        self.type: str = type
        self.options: List = []
        self.label: str = label

    def add_option(self, value, text):
        self.options.append((value, text))

    def get(self):
        ret = f'<label for="{self.id}">{self.label}</label>\n'
        if self.type == Input.SELECT:
            ret += f'<select name="{self.id}" id="{self.id}">\n'
            for opt in self.options:
                ret += f'<option value="{opt[0]}">{opt[1]}</option>\n'
            ret += "</select>\n"
        else:
            ret += f'<input type="{self.type}" id="{self.id}" name="{self.id}">\n'
        return ret


class Content:
    def __init__(self, summary, button, headers) -> None:
        self.summary: str = summary
        self.open: str = ""
        self.button: str = button
        self.forms: List[Input] = []
        self.headers: List[str] = headers
        self.results: List[Any] = []


content: List[Content] = [
    Content(
        "List homes that have been sold multiple times",
        "list_homes_sold_multiple_times",
        ["Address", "Count"],
    ),
    Content(
        "List owners that own apartments and mansions",
        "find_owners_who_own_apartments_and_mansions",
        ["Owner"],
    ),
    Content(
        "List owners that sold a home at one point",
        "find_all_homes_owner_used_to_own",
        ["Owner"],
    ),
    Content(
        "List all homes below a price in a given city",
        "list_homes_below_price_in_city",
        ["Address", "Price"],
    ),
    Content(
        "Return the most expensive home an owner ever bought",
        "find_highest_selling_home",
        ["Price", "Address"],
    ),
    Content(
        "List all homes with only appliances of one make",
        "find_homes_with_appliances_of_make",
        ["Address", "Appliances"],
    ),
    Content(
        "Return a Agents total commission earned",
        "total_commission_by_agent",
        ["Commission"],
    ),
    Content(
        "Return owner with most expensive home in city",
        "list_owners_with_most_expensive_homes_in_city",
        ["Owner", "Price", "Address"],
    ),
    Content(
        "List homes by owner and city",
        "list_homes_by_owner_and_city",
        ["Address", "Home"],
    ),
]


def setOpen():
    for c in content:
        c.open = ""
    return "open"


# pre defined Queries
@app.route("/queries", methods=["GET", "POST"])
def queries():
    cities = locations_collection.distinct(db.LOCATION.city)
    owners = list(owners_collection.find())
    makes = list(appliances_collection.distinct(db.APPLIANCE.make))
    agents = list(agents_collection.find())

    # add inputs for list_homes_below_price_in_city
    content[3].forms.clear()
    content[3].forms.append(Input(Input.NUMBER, "Price", "price_3"))
    i = Input(Input.SELECT, "City", "city_3")
    i.add_option("", "Pick a City")
    for c in cities:
        i.add_option(c, c)
    content[3].forms.append(i)

    # add inputs for find_highest_selling_home
    content[4].forms.clear()
    i = Input(Input.SELECT, "Owner", "owner_4")
    i.add_option("", "Pick an Owner")
    for o in owners:
        i.add_option(o["_id"], f"{o['first_name']} {o["last_name"]}")
    content[4].forms.append(i)

    # add inputs for find_homes_with_appliances_of_make
    content[5].forms.clear()
    i = Input(Input.SELECT, "Make", "make_5")
    i.add_option("", "Pick a Make")
    for m in makes:
        i.add_option(m, m)
    content[5].forms.append(i)

    # add inputs for total_commission_by_agent
    content[6].forms.clear()
    i = Input(Input.SELECT, "Agent", "agent_6")
    i.add_option("", "Pick an Agent")
    for a in agents:
        i.add_option(a["_id"], f'{a["first_name"]} {a["last_name"]}')
    content[6].forms.append(i)

    # add inputs for list_owners_with_most_expensive_homes_in_city
    content[7].forms.clear()
    i = Input(Input.SELECT, "City", "city_7")
    i.add_option("", "Pick a City")
    for c in cities:
        i.add_option(c, c)
    content[7].forms.append(i)

    # add inputs for list_homes_by_owner_and_city
    content[8].forms.clear()
    i = Input(Input.SELECT, "City", "city_8")
    i.add_option("", "Pick a City")
    for c in cities:
        i.add_option(c, c)
    content[8].forms.append(i)

    i = Input(Input.SELECT, "Owner", "owner_8")
    i.add_option("", "Pick an Owner")
    for o in owners:
        i.add_option(o["_id"], f"{o['first_name']} {o["last_name"]}")
    content[8].forms.append(i)

    if request.method == "POST":
        if "list_homes_sold_multiple_times" in request.values.keys():
            c = content[0]
            c.results.clear()

            res = q.list_homes_sold_multiple_times()

            for r in res:
                addr = r["addr"]
                unit = f"</br>{addr['unit_number']}" if addr["unit_number"] else ""
                c.results.append(
                    [
                        f"{addr['street_number']} {addr['street']}{unit}</br>{addr['city']}, {addr['state']} {addr['zip']}",
                        r["times_sold"],
                    ]
                )
            c.open = setOpen()

        if "find_owners_who_own_apartments_and_mansions" in request.values.keys():
            c = content[1]
            c.results.clear()

            res = q.find_owners_who_own_apartments_and_mansions()

            for r in res:
                c.results.append([f"{r['first_name']} {r['last_name']}"])

            c.open = setOpen()

        if "find_all_homes_owner_used_to_own" in request.values.keys():
            c = content[2]
            c.results.clear()

            res = q.find_all_homes_owner_used_to_own()

            for r in res:
                c.results.append([f"{r['first_name']} {r['last_name']}"])

            c.open = setOpen()

        if "list_homes_below_price_in_city" in request.values.keys():
            c = content[3]
            c.results.clear()

            res = q.list_homes_below_price_in_city(
                float(request.values.get("price_3")), request.values.get("city_3")
            )
            for r in res:
                addr = r["address"]
                unit = f"</br>{addr['unit_number']}" if addr["unit_number"] else ""
                c.results.append(
                    [
                        f"{addr['street_number']} {addr['street']}{unit}</br>{addr['city']}, {addr['state']} {addr['zip']}",
                        r["transactions"][0]["price"],
                    ]
                )

            c.open = setOpen()

        if "find_highest_selling_home" in request.values.keys():
            c = content[4]
            c.results.clear()

            res = q.find_highest_selling_home(ObjectId(request.values.get("owner_4")))

            for r in res:
                addr = r["home_details"]["location"]
                unit = f"</br>{addr['unit_number']}" if addr["unit_number"] else ""
                c.results.append(
                    [
                        r["price"],
                        f"{addr['street_number']} {addr['street']}{unit}</br>{addr['city']}, {addr['state']} {addr['zip']}",
                    ]
                )

            c.open = setOpen()

        if "find_homes_with_appliances_of_make" in request.values.keys():
            c = content[5]
            c.results.clear()

            res = q.find_homes_with_appliances_of_make(request.values.get("make_5"))

            for r in res:
                addr = r["location"]
                unit = f"</br>{addr['unit_number']}" if addr["unit_number"] else ""
                appliances = ""
                for a in r["appliances"]:
                    appliances += (
                        f'{a["name"]} - {a["make"]} {a["model"]} ({a['year']})</br>'
                    )
                c.results.append(
                    [
                        f"{addr['street_number']} {addr['street']}{unit}</br>{addr['city']}, {addr['state']} {addr['zip']}",
                        appliances,
                    ]
                )

            c.open = setOpen()

        if "total_commission_by_agent" in request.values.keys():
            c = content[6]
            c.results.clear()

            res = q.total_commission_by_agent(request.values.get("agent_6"))
            for r in res:
                c.results.append([r["total_commission"]])

            c.open = setOpen()

        if "list_owners_with_most_expensive_homes_in_city" in request.values.keys():
            c = content[7]
            c.results.clear()

            res = q.list_owners_with_most_expensive_homes_in_city(
                request.values.get("city_7")
            )
            for r in res:
                addr = r["location"]
                unit = f"</br>{addr['unit_number']}" if addr["unit_number"] else ""
                c.results.append(
                    [
                        r["owner_name"],
                        r["home_value"],
                        f"{addr['street_number']} {addr['street']}{unit}</br>{addr['city']}, {addr['state']} {addr['zip']}",
                    ]
                )

            c.open = setOpen()

        if "list_homes_by_owner_and_city" in request.values.keys():
            c = content[8]
            c.results.clear()

            res = q.list_homes_by_owner_and_city(
                request.values.get("owner_8"), request.values.get("city_8")
            )

            for r in res:
                addr = r["location"]
                unit = f"</br>{addr['unit_number']}" if addr["unit_number"] else ""

                appliances = ""
                for a in r["appliances"]:
                    appliances += (
                        f'{a["name"]} - {a["make"]} {a["model"]} ({a['year']})</br>'
                    )

                c.results.append(
                    [
                        f"{addr['street_number']} {addr['street']}{unit}</br>{addr['city']}, {addr['state']} {addr['zip']}",
                        f"Floor space: {r['floor_space']}</br> \
                            Floors: {r['floors']}</br> \
                            Bedrooms: {r['bed_rooms']}</br> \
                            Bathrooms: {r['bath_rooms']}</br> \
                            Type: {r['home_type']}</br> \
                            Year Constructed: {r['year_constructed']}</br> \
                            Appliances:</br> \
                            {appliances}",
                    ]
                )

            c.open = setOpen()

    return render_template("queries.html", content=content)
