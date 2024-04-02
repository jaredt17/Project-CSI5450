import json
import random
from datetime import datetime, timedelta

import db

from pymongo import MongoClient

def decode_date(dct):
    if 'date' in dct:
        dct['date'] = datetime.strptime(dct['date'], '%Y-%m-%d')
    return dct

def init_db(path: str = 'mock_data.json'):

    with open(path) as f:
        data = json.load(f, object_hook=decode_date)
    
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
    owners_collection.insert_many(data[db.TABLES.OWNERS])


    owners = list(owners_collection.find())
    locations = list(locations_collection.find())
    appliances = list(appliances_collection.find())

    # fix companies

    companies_collection.insert_many(data[db.TABLES.COMPANIES])

    companies_collection.update_one(
        {db.COMPANY.name: "BrigthBridge Realty"},
        { "$set": {db.COMPANY.location: locations[2]}})
    
    companies_collection.update_one(
        {db.COMPANY.name: "CrestView Estates"},
        { "$set": {db.COMPANY.location: locations[3]}})
    
    companies_collection.update_one(
        {db.COMPANY.name: "MapleOak Properties"},
        { "$set": {db.COMPANY.location: locations[4]}})
    
    companies = list(companies_collection.find())


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

    agents_collection.update_one(
        {db.AGENT.first_name: "Viljo", db.AGENT.last_name: "Wagner"},
        { "$push": {db.AGENT.companies: companies[0]}}
    )

    agents_collection.update_one(
        {db.AGENT.first_name: "Jared", db.AGENT.last_name: "Teller"},
        { "$push": {db.AGENT.companies: companies[1]}}
    )
    agents_collection.update_one(
        {db.AGENT.first_name: "Jon", db.AGENT.last_name: "Snow"},
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
    homes_collection.update_one(
        {db.HOME.year_constructed: 2001},
        { "$set": {db.HOME.owner: owners[4],
                   db.HOME.location: locations[5],
                   db.HOME.appliances: appliances[3:4]}}
    )
    
    homes_collection.update_one(
        {db.HOME.year_constructed: 2008},
        { "$set": {db.HOME.owner: owners[4],
                   db.HOME.location: locations[6],
                   db.HOME.appliances: appliances[2:3]}}
    )

    homes_collection.update_one(
        {db.HOME.year_constructed: 2019},
        { "$set": {db.HOME.owner: owners[3],
                   db.HOME.location: locations[4],
                   db.HOME.appliances: appliances[1:3]}}
    )

    homes = list(homes_collection.find())

    # # fix transactions
    # transactions_collection.insert_many(data[db.TABLES.TRANSACTIONS])

    # transactions_collection.update_one(
    #     {db.TRANSACTION.date: "2023-01-15"},
    #     {"$set": {db.TRANSACTION.home: homes[0],
    #               db.TRANSACTION.owner: owners[0],
    #               db.TRANSACTION.agent: agents[0],
    #               db.TRANSACTION.company: companies[0]}}
    # )

    # transactions_collection.update_one(
    #     {db.TRANSACTION.date: "2023-02-20"}, 
    #     {"$set": {db.TRANSACTION.home: homes[1],
    #               db.TRANSACTION.owner: owners[1],
    #               db.TRANSACTION.agent: agents[1],
    #               db.TRANSACTION.company: companies[2]}}
    # )

    # Randomly generate transactions
    for _ in range(5):  # Number of transactions to create
        home = random.choice(homes)
        seller = random.choice(owners)
        buyer = random.choice(owners)
        agent = random.choice(agents)
        company = random.choice(companies)

        # print(home)
        
        # Random date within the last year
        transaction_date = datetime.now() - timedelta(days=random.randint(0, 365))
        
        # Random price
        transaction_price = round(random.uniform(100000, 300000), 2)
        
        transaction = {
            db.TRANSACTION.seller: seller['_id'],
            db.TRANSACTION.buyer: buyer['_id'],
            db.TRANSACTION.home: home['_id'],
            db.TRANSACTION.agent: agent['_id'],
            db.TRANSACTION.company: company['_id'],
            db.TRANSACTION.date: transaction_date,
            db.TRANSACTION.price: transaction_price
        }
        
        transactions_collection.insert_one(transaction)

    # Randomly generate transactions
    for _ in range(6,10,1):  # Number of transactions to create
        home = random.choice(homes)
        seller = random.choice(owners)
        buyer = random.choice(owners)
        agent = random.choice(agents)
        company = random.choice(companies)

        # print(home)
        
        # Random date within the last year
        transaction_date = datetime.now() - timedelta(days=random.randint(0, 365))
        
        # Random price
        transaction_price = round(random.uniform(100000, 300000), 2)
        
        transaction = {
            db.TRANSACTION.seller: seller['_id'],
            db.TRANSACTION.buyer: None,
            db.TRANSACTION.home: home['_id'],
            db.TRANSACTION.agent: agent['_id'],
            db.TRANSACTION.company: company['_id'],
            db.TRANSACTION.date: transaction_date,
            db.TRANSACTION.price: transaction_price
        }
        
        transactions_collection.insert_one(transaction)