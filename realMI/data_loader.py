import json

# Function to insert mock data into the HOMES collection
def load_mock():
    with open('mock_data.json') as f:
        data = json.load(f)
    return data

# # homes_collection.insert_many(homes_data)

    
# # Function to insert mock data into the LOCATIONS collection
    
# def insert_mock_locations():
#     locations_collection = db[TABLES.LOCATIONS]
#     with open('mock_data/locations.json') as f:
#         locations_data = json.load(f)
#     locations_collection.insert_many(locations_data)

# # Function to insert mock data into the APPLIANCES collection
# def insert_mock_appliances():
#     appliances_collection = db[TABLES.APPLIANCES]
#     with open('mock_data/appliances.json') as f:
#         appliances_data = json.load(f)
#     appliances_collection.insert_many(appliances_data)

# # Function to insert mock data into the AGENTS collection
# def insert_mock_agents():
#     agents_collection = db[TABLES.AGENTS]
#     with open('mock_data/agents.json') as f:
#         agents_data = json.load(f)
#     agents_collection.insert_many(agents_data)

# # Function to insert mock data into the OWNERS collection
# def insert_mock_owners():
#     owners_collection = db[TABLES.OWNERS]
#     with open('mock_data/owners.json') as f:
#         owners_data = json.load(f)
#     owners_collection.insert_many(owners_data)

# # Function to insert mock data into the TRANSACTIONS collectioN
# def insert_mock_transactions():
#     transactions_collection = db[TABLES.TRANSACTIONS]
#     with open('mock_data/transactions.json') as f:
#         transactions_data = json.load(f)
#     transactions_collection.insert_many(transactions_data)

# # Function to insert mock data into the COMPANIES collection
# def insert_mock_companies():
#     companies_collection = db[TABLES.COMPANIES]
#     with open('mock_data/companies.json') as f:
#         companies_data = json.load(f)
#     companies_collection.insert_many(companies_data)