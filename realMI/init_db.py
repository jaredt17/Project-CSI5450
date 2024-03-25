import json

import db

from pymongo import MongoClient

def init_db(path: str = 'mock_data.json'):

    with open(path) as f:
        data = json.load(f)
    
    client = MongoClient()
    client.drop_database(db.DB)
    database = client[db.DB]

    # Define collections
    homes_collection = database[db.TABLES.HOMES]
    locations_collection = database[db.TABLES.LOCATIONS]
    appliances_collection = database[db.TABLES.APPLIANCES]
    agents_collection = database[db.TABLES.AGENTS]
    owners_collection = database[db.TABLES.OWNERS]
    transactions_collection = database[db.TABLES.TRANSACTIONS]
    companies_collection = database[db.TABLES.COMPANIES]

    # Loading Data
    appliances_collection.insert_many(data[db.TABLES.APPLIANCES])
    locations_collection.insert_many(data[db.TABLES.LOCATIONS])
    companies_collection.insert_many(data[db.TABLES.COMPANIES])
    owners_collection.insert_many(data[db.TABLES.OWNERS])


    owners = list(owners_collection.find())
    locations = list(locations_collection.find())
    companies = list(companies_collection.find())
    appliances = list(appliances_collection.find())


    # fix agents
    agents_collection.insert_many(data[db.TABLES.AGENTS])

    agents_collection.update_one(
        {db.AGENT.first_name: "John", db.AGENT.last_name: "Doe"},
        { "$set": {db.AGENT.companies: companies[0:2]}}
    )

    agents_collection.update_one(
        {db.AGENT.first_name: "Jane", db.AGENT.last_name: "Smith"},
        { "$push": {db.AGENT.companies: companies[2]}}
    )

    agents = list(agents_collection.find())


    # fix homes
    homes_collection.insert_many(data[db.TABLES.HOMES])

    homes_collection.update_one(
        {db.HOME.year_constructed: 1998},
        { "$set": {db.HOME.owner: owners[0], 
                   db.HOME.location: locations[0],
                   db.HOME.appliances: appliances[0:3]}}
    )

    homes_collection.update_one(
        {db.HOME.year_constructed: 2005},
        { "$set": {db.HOME.owner: owners[1],
                   db.HOME.location: locations[1],
                   db.HOME.appliances: appliances}}
    )

    homes = list(homes_collection.find())

    # fix transactions
    transactions_collection.insert_many(data[db.TABLES.TRANSACTIONS])

    transactions_collection.update_one(
        {db.TRANSACTION.date: "2023-01-15"},
        {"$set": {db.TRANSACTION.home: homes[0],
                  db.TRANSACTION.owner: owners[0],
                  db.TRANSACTION.agent: agents[0],
                  db.TRANSACTION.company: companies[0]}}
    )

    transactions_collection.update_one(
        {db.TRANSACTION.date: "2023-02-20"}, 
        {"$set": {db.TRANSACTION.home: homes[1],
                  db.TRANSACTION.owner: owners[1],
                  db.TRANSACTION.agent: agents[1],
                  db.TRANSACTION.company: companies[2]}}
    )
