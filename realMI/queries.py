from pymongo import MongoClient
from bson import ObjectId
import db

from bson import ObjectId

# Queries

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


def list_homes_by_owner_and_city(owner, city):
    """List all the homes owned by a given owner in a given city."""
    pass

def list_homes_sold_multiple_times():
    """List all the homes that were sold more than once.""" 
    duplicates = transactions_collection.aggregate({
        db.group: {
            "_id": "$home",
            "count": {db.sum: 1}
        },
        db.match: {
            "count": {db.greater_than: 1}
        }
    })

    return duplicates


def find_highest_selling_home(owner):
    """Find the most expensive home an owner ever bought."""
    pass

def find_homes_with_appliances_of_make(make):
    """Find all the homes that include all e appliances by the same maker."""
    pass

def find_all_homes_owner_used_to_own():
    """Find owners who do not own the homes they used to own. """
    used = transactions_collection.aggregate({
        db.group: {
            "_id": "$seller"
        }
    })

    return used


def total_commission_by_agent(agent_id):
    """Find the total commissions earned by an agent. Assume that commission earned is on the purchased price of a home he/she sells. """
    pipeline = [
    # Match to filter transactions by the specific agent's _id
    {
        db.match: {
            "agent": agent_id  # Assuming this is how you reference the agent in transactions
        }
    },
    # Lookup to join with the COMPANY collection to get the commission percentage
    # This assumes that the transaction includes the specific company _id for the transaction
    {
        db.lookup: {
            "from": "COMPANY",
            "localField": "company",  # Field in TRANSACTION that references the company _id
            "foreignField": "_id",  # Matching against the _id in COMPANY
            "as": "company_details"
        }
    },
    {db.unwind: "$company_details"},
    # Calculate the commission amount for each transaction
    {
        "$addFields": {
            "calculated_commission": {
                db.multiply: ["$price", {db.divide: ["$company_details.commission", 100]}]
            }
        }
    },
    # Group by agent to sum the total commission
    {
        db.group: {
            "_id": "$agent",  # Group by the agent's _id
            "total_commission": {db.sum: "$calculated_commission"}
        }
    },
    # Optionally, join again with the AGENT collection to enrich the agent's identity information
    {
        db.lookup: {
            "from": "AGENT",
            "localField": "_id",
            "foreignField": "_id",
            "as": "agent_details"
        }
    },
    {db.unwind: "$agent_details"},
    # Format the output to display the agent's name and their total commission
    {
        db.project: {
            "_id": 0,
            "agent_name": {
                db.concat: ["$agent_details.first_name", " ", "$agent_details.last_name"]
            },
            "total_commission": 1
        }
    }]

    # Execute aggregation pipeline
    result = transactions_collection.aggregate(pipeline)

    return result

def find_owners_who_own_apartments_and_mansions():
    """Find people who own apartments as well as mansions. """
    pipeline = [
    # Step 1: Filter homes that are either apartments or mansions
    {
        "$match": {
            "home_type": {"$in": ["apartment", "mansion"]}
        }
    },
    # Step 2: Group by owner, and collect the types of homes each owner has
    {
        "$group": {
            "_id": "$owner",  # Assuming 'owner' references the OWNER collection
            "home_types": {"$addToSet": "$home_type"}
        }
    },
    # Step 3: Filter owners who own both apartments and mansions
    {
        "$match": {
            "home_types": {"$all": ["apartment", "mansion"]}
        }
    },
    # Optionally, you might want to lookup the owner information
    {
        "$lookup": {
            "from": "OWNER",
            "localField": "_id",
            "foreignField": "_id",
            "as": "owner_details"
        }
    },
    # Projecting the result to format it nicely
    {
        "$project": {
            "_id": 0,
            "owner_id": "$_id",
            "owner_details": 1
        }
    }]

    # Execute aggregation pipeline
    result = homes_collection.aggregate(pipeline)

    return result

def list_homes_below_price_in_city(price, city):
    """List all the homes below a price in a given city."""
    # TODO: figure out hwo for_sale in HOMES works.
    pass

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
    }]

    # Execute aggregation pipeline
    result = homes_collection.aggregate(pipeline)

    return result

def find_home_for_sale(**params):
    """Find homes that up for sale in a given city that meet certain buyer choices such as number of bedrooms, baths, etc"""
    pass
