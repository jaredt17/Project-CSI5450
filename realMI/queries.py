from pymongo import MongoClient
from bson import ObjectId
import db

from bson import ObjectId

# Queries

client = MongoClient()
# client.drop_database(db.DB)
database = client['realmi']

# Define collections
homes_collection = database['HOMES']
locations_collection = database["LOCATIONS"]
appliances_collection = database["APPLIANCES"]
agents_collection = database["AGENTS"]
owners_collection = database["OWNERS"]
transactions_collection = database["TRANSACTIONS"]
companies_collection = database["COMPANIES"]


def list_homes_by_owner_and_city(owner, city):
    """List all the homes owned by a given owner in a given city."""
    pass

def list_homes_sold_multiple_times():
    pipeline = [
        {
            '$group': {
                '_id': '$home', 
                'count': {
                    '$sum': 1
                }
            }
        }, {
            '$match': {
                'count': {
                    '$gt': 1
                }
            }
        }, {
            '$lookup': {
                'from': 'HOMES', 
                'localField': '_id', 
                'foreignField': '_id', 
                'as': 'home_details'
            }
        }, {
            '$unwind': '$home_details'
        }, {
            '$project': {
                '_id': 0, 
                'address': '$home_details.location', 
                'times_sold': '$count'
            }
        }
    ]
    duplicates = transactions_collection.aggregate(pipeline)
    return list(duplicates)

# CARLO TO DO
def find_highest_selling_home(owner):
    """Find the most expensive home an owner ever bought."""
    pass

# CARLO TO DO
def find_homes_with_appliances_of_make(make):
    """Find all the homes that include all e appliances by the same maker."""
    pass

# CARLO TO DO
def find_all_homes_owner_used_to_own():
    """Find owners who do not own the homes they used to own. """
    
    pass

# Fully implemented and working into HTML
def total_commission_by_agent(agent_id_str):
    # convert str to objectID
    agent_id = ObjectId(agent_id_str)
    # print(agent_id)
    """Find the total commissions earned by an agent. Assume that commission earned is on the purchased price of a home he/she sells."""
    pipeline = [
        {
            '$match': {
                'agent': agent_id
            }
        }, {
            '$lookup': {
                'from': 'COMPANIES', 
                'localField': 'company', 
                'foreignField': '_id', 
                'as': 'company_details'
            }
        }, {
            '$unwind': {
                'path': '$company_details'
            }
        }, {
            '$addFields': {
                'calculated_commission': {
                    '$multiply': [
                        '$price', {
                            '$divide': [
                                '$company_details.commission', 100
                            ]
                        }
                    ]
                }
            }
        }, {
            '$group': {
                '_id': '$agent', 
                'total_commission': {
                    '$sum': '$calculated_commission'
                }
            }
        }, {
            '$lookup': {
                'from': 'AGENTS', 
                'localField': '_id', 
                'foreignField': '_id', 
                'as': 'agent_details'
            }
        }, {
            '$unwind': {
                'path': '$agent_details'
            }
        }, {
            '$project': {
                '_id': 0, 
                'agent_name': {
                    '$concat': [
                        '$agent_details.first_name', ' ', '$agent_details.last_name'
                    ]
                }, 
                'total_commission': 1
            }
        }
    ]

    # Execute aggregation pipeline
    result = transactions_collection.aggregate(pipeline)
    return list(result)  # Convert cursor to list to consume its contents

def find_owners_who_own_apartments_and_mansions():
    """Find people who own apartments as well as mansions. """
    pipeline = [
        {
            '$match': {
                'home_type': {
                    '$in': [
                        'apartment', 'mansion'
                    ]
                }
            }
        }, {
            '$group': {
                '_id': '$owner', 
                'home_types': {
                    '$addToSet': '$home_type'
                }
            }
        }, {
            '$match': {
                'home_types': {
                    '$all': [
                        'apartment', 'mansion'
                    ]
                }
            }
        }, {
            '$project': {
                '_id': 0, 
                'first_name': '$_id.first_name', 
                'last_name': '$_id.last_name'
            }
        }
    ]

    # Execute aggregation pipeline
    result = homes_collection.aggregate(pipeline)
    return list(result)

def list_homes_below_price_in_city(price, city):
    """List all the homes below a price in a given city."""
    pipeline = [
        {
            "$lookup": {
                "from": "TRANSACTION",
                "localField": "_id",  # Assuming home _id is what TRANSACTION references
                "foreignField": "home",  # 'home' in TRANSACTION refers to HOME _id
                "as": "transactions"
            }
        },
        # Step 2: Filter by city
        {
            "$match": {
                "location.city": city
            }
        },
        # Unwind transactions to filter individually
        {
            "$unwind": "$transactions"
        },
        # Step 3: Filter transactions below the specified price
        {
            "$match": {
                "transactions.price": {"$lt": price}
            }
        },
        # Optional: Group by home to aggregate transactions (if you want to compile transactions per home)
        {
            "$group": {
                "_id": "$_id",
                "location": {"$first": "$location"},
                "transactions": {"$push": "$transactions"}
            }
        },
        # Optional: Sort by transaction price
        {
            "$sort": {
                "transactions.price": 1  # Adjust according to your needs
            }
        },
        # Project/format the output
        {
            "$project": {
                "_id": 0,
                "address": "$location",
                "transactions": 1
            }
        }
    ]

    result = homes_collection.aggregate(pipeline)

    return result


def list_owners_with_most_expensive_homes_in_city(city):
    """List owners who own all the most expensive homes in a given city"""
    pipeline = [
        # Step 1: Join HOME collection with TRANSACTION to get home prices
        {
            "$lookup": {
                "from": "TRANSACTION",
                "localField": "_id",  # Assuming home _id is what TRANSACTION references
                "foreignField": "home",  # Assuming 'home' in TRANSACTION refers to HOME _id
                "as": "transactions"
            }
        },
        # Optional: If you want only the latest transaction for each home
        {
            "$addFields": {
                "latest_transaction": {"$arrayElemAt": ["$transactions", -1]}  # Assuming the last transaction is the latest
            }
        },
        # Step 2: Filter by city
        {
            "$match": {
                "location.city": city
            }
        },
        # Step 3: Sort by home value (price in the latest transaction)
        {
            "$sort": {
                "latest_transaction.price": -1  # Adjust field path if your data structure is different
            }
        },
        # Step 4: Project/format the output
        {
            "$project": {
                "_id": 0,
                "owner_name": {"$concat": ["$owner.first_name", " ", "$owner.last_name"]},
                "home_value": "$latest_transaction.price",
                "city": "$location.city"
            }
        }
    ]

    # Execute aggregation pipeline
    result = homes_collection.aggregate(pipeline)

    return result

def find_home_for_sale(**params):
    """Find homes that up for sale in a given city that meet certain buyer choices such as number of bedrooms, baths, etc"""

    matches = { f"home_details.{k}": v for k, v in params}

    pipeline = [
        # Step 1: Filter transactions where the home is for sale (seller is null)
        {
            "$match": {
                "seller": None  # Finding transactions with no seller (home is for sale)
            }
        },
        # Step 2: Join with HOME collection to get home details
        {
            "$lookup": {
                "from": "HOME",
                "localField": "home",  # Assuming 'home' in TRANSACTION refers to HOME _id
                "foreignField": "_id",  # Matching _id in HOME collection
                "as": "home_details"
            }
        },
        {"$unwind": "$home_details"},  # Deconstruct the home_details array
        # Step 3: Filter homes based on the specified number of bedrooms and bathrooms
        {
            "$match": matches
        },
        # Project/format the output
        {
            "$project": {
                "_id": 0,
                "home_id": "$home",  # Show home id
                "bedrooms": "$home_details.bed_rooms",
                "bathrooms": "$home_details.bath_rooms",
                "for_sale": {"$ifNull": ["$seller", True]},  # Indicate the home is for sale
                "location": "$home_details.location",  # Assuming you store location info in the HOME collection
                "price": "$price"  # Assuming price is in the TRANSACTION
            }
        }
    ]

    result = transactions_collection.aggregate(pipeline)

    return pipeline
