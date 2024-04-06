#!/usr/bin/python3

from pymongo import MongoClient
from realMI import db
from bson import json_util
import json

client = MongoClient()
# client.drop_database(db.DB)
database = client[db.DB]

col_names = database.list_collection_names()

json_db = {}

for col in col_names:
    json_db[col] = list(database[col].find())

print(json_db)

with open("./realMI/db_export.json", "w") as dbw:
    json.dump(json_util.dumps(json_db), dbw)

