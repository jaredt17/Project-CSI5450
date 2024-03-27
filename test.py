from pymongo import MongoClient
from realMI import db
from bson import ObjectId

client = MongoClient()

database = client['realmi']

appliance = database[db.TABLES.APPLIANCES]
# Define collections
homes_collection = database['HOMES']
locations_collection = database["LOCATIONS"]
appliances_collection = database["APPLIANCES"]
agents_collection = database["AGENTS"]
owners_collection = database["OWNERS"]
transactions_collection = database["TRANSACTIONS"]
companies_collection = database["COMPANIES"]

ret = appliance.find()
print(ret)




# Fetch the transaction by its ID
transaction = transactions_collection.find_one({"_id": ObjectId("6603a24787477a7fbcfc12e3")})

if transaction:
    # Fetch the home using the 'home' field from the transaction
    home = homes_collection.find_one({"_id": transaction['home']})

    if home:

        print("Transaction Details:")
        print(f"Date: {transaction['date']}")
        print(f"Price: {transaction['price']}")

        print("\nAssociated Home Details:")
        print(f"Floor Space: {home['floor_space']}")
        print(f"Bedrooms: {home['bed_rooms']}")
        print(f"Bathrooms: {home['bath_rooms']}")
        # Add more attributes as needed
else:
    print("Transaction not found.")