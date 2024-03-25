from pymongo import MongoClient
from realMI import db

client = MongoClient()

database = client['realmi']

appliance = database[db.TABLES.APPLIANCES]
ret = appliance.find()
print(ret)