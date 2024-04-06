#!/usr/bin/python3

from pymongo import MongoClient
from realMI import db
from bson import json_util
import json

client = MongoClient()
client.drop_database(db.DB)
database = client[db.DB]

with open("db_export.json", "r") as dbw:
    in_db = json.load(dbw)

ac_db: dict = json_util.loads(in_db)

for k in ac_db.keys():
    col = database.create_collection(k)
    col.insert_many(ac_db[k])

client.close()