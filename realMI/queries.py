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
        "$group": {
            "_id": "$home",
            "count": {"$sum": 1}
        },
        "$match": {
            "count": {"$gt": 1}
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
    pass

def total_commission_by_agent(agent):
    """Find the total commissions earned by an agent. Assume that commission earned is on the purchased price of a home he/she sells. """
    pass

def find_owners_who_own_apartments_and_mansions():
    """Find people who own apartments as well as mansions. """
    pass

def list_homes_below_price_in_city(price, city):
    """List all the homes below a price in a given city."""
    pass

def list_owners_with_most_expensive_homes_in_city(city):
    """List owners who own all the most expensive homes in a given city"""
    pass

def find_home_for_sale(**params):
    """Find homes that up for sale in a given city that meet certain buyer choices such as number of bedrooms, baths, etc"""
    pass
