from bson import ObjectId

# Queries

class Queries:

    def __init__(self, database) -> None:
        self.homes = database["HOMES"]
        self.locations = database["LOCATIONS"]
        self.appliances = database["APPLIANCES"]
        self.agents = database["AGENTS"]
        self.owners = database["OWNERS"]
        self.transactions = database["TRANSACTIONS"]
        self.companies = database["COMPANIES"]

    # Works in Mongo - need to add to website
    def list_homes_by_owner_and_city(self, owner_id, city):
        """List all the homes owned by a given owner in a given city."""
        # Convert owner_id to ObjectId if it's passed as a string
        if isinstance(owner_id, str):
            owner_id = ObjectId(owner_id)

        pipeline = [{"$match": {"owner._id": owner_id, "location.city": city}}]

        return list(self.homes.aggregate(pipeline))


    # WORKING - todo add to website
    def list_homes_sold_multiple_times(self):
        pipeline = [
            {"$group": {"_id": "$home", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {
                "$lookup": {
                    "from": "HOMES",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "home_details",
                }
            },
            {"$unwind": "$home_details"},
            {
                "$project": {
                    "_id": 0,
                    "addr": "$home_details.location",
                    "times_sold": "$count",
                }
            },
        ]

        return list(self.transactions.aggregate(pipeline))


    # WORKING testing - to add to website
    def find_highest_selling_home(self, owner):
        """Find the most expensive home an owner ever bought."""
        pipeline = [
            {"$match": {"buyer": owner}},
            {"$sort": {"price": -1}},
            {"$limit": 1},
            {
                "$lookup": {
                    "from": "HOMES",
                    "localField": "home",
                    "foreignField": "_id",
                    "as": "home_details",
                }
            },
            {"$unwind": "$home_details"},
            {"$project": {"_id": 0, "price": 1, "home_details": 1}},
        ]
        return list(self.transactions.aggregate(pipeline))


    # WORKING - to add to website
    def find_homes_with_appliances_of_make(self, make):
        """Find all the homes that include all e appliances by the same maker."""
        pipeline = [
            {"$match": {"appliances.make": make}},
            {
                "$addFields": {
                    "allAppliancesMatch": {
                        "$allElementsTrue": {
                            "$map": {
                                "input": "$appliances",
                                "as": "appliance",
                                "in": {"$eq": ["$$appliance.make", make]},
                            }
                        }
                    }
                }
            },
            {"$match": {"allAppliancesMatch": True}},
        ]

        return list(self.homes.aggregate(pipeline))


    # WORKING - to add to website
    def find_all_homes_owner_used_to_own(self):
        """Find owners who do not own the homes they used to own."""

        pipeline = [
            {"$group": {"_id": "$seller"}},
            {
                "$lookup": {
                    "from": "OWNERS",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "owner_details",
                }
            },
            {"$unwind": "$owner_details"},
            {
                "$project": {
                    "_id": 0,
                    "first_name": "$owner_details.first_name",
                    "last_name": "$owner_details.last_name",
                }
            },
        ]
        return list(self.transactions.aggregate(pipeline))


    # Fully implemented and working into HTML
    def total_commission_by_agent(self, agent_id_str):
        # convert str to objectID
        agent_id = ObjectId(agent_id_str)
        # print(agent_id)
        """Find the total commissions earned by an agent. Assume that commission earned is on the purchased price of a home he/she sells."""
        pipeline = [
            {"$match": {"agent": agent_id}},
            {
                "$lookup": {
                    "from": "COMPANIES",
                    "localField": "company",
                    "foreignField": "_id",
                    "as": "company_details",
                }
            },
            {"$unwind": {"path": "$company_details"}},
            {
                "$addFields": {
                    "calculated_commission": {
                        "$multiply": [
                            "$price",
                            {"$divide": ["$company_details.commission", 100]},
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$agent",
                    "total_commission": {"$sum": "$calculated_commission"},
                }
            },
            {
                "$lookup": {
                    "from": "AGENTS",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "agent_details",
                }
            },
            {"$unwind": {"path": "$agent_details"}},
            {
                "$project": {
                    "_id": 0,
                    "agent_name": {
                        "$concat": [
                            "$agent_details.first_name",
                            " ",
                            "$agent_details.last_name",
                        ]
                    },
                    "total_commission": 1,
                }
            },
        ]

        # Execute aggregation pipeline
        result = self.transactions.aggregate(pipeline)
        return list(result)  # Convert cursor to list to consume its contents


    # Working and Added
    def find_owners_who_own_apartments_and_mansions(self):
        """Find people who own apartments as well as mansions."""
        pipeline = [
            {"$match": {"home_type": {"$in": ["apartment", "mansion"]}}},
            {"$group": {"_id": "$owner", "home_types": {"$addToSet": "$home_type"}}},
            {"$match": {"home_types": {"$all": ["apartment", "mansion"]}}},
            {
                "$project": {
                    "_id": 0,
                    "first_name": "$_id.first_name",
                    "last_name": "$_id.last_name",
                }
            },
        ]

        # Execute aggregation pipeline
        result = self.homes.aggregate(pipeline)
        return list(result)


    # WORKING - to do add to website
    def list_homes_below_price_in_city(self, price, city):
        """List all the homes below a price in a given city."""
        pipeline = [
            {
                "$lookup": {
                    "from": "TRANSACTIONS",
                    "localField": "_id",
                    "foreignField": "home",
                    "as": "transactions",
                }
            },
            {"$match": {"location.city": city}},
            {"$unwind": {"path": "$transactions", "preserveNullAndEmptyArrays": True}},
            {
                "$match": {
                    "$or": [
                        {"transactions.buyer": {"$exists": False}},
                        {"transactions.buyer": None},
                    ],
                    "transactions.price": {"$lt": price},
                }
            },
            {
                "$group": {
                    "_id": "$_id",
                    "location": {"$first": "$location"},
                    "transactions": {"$push": "$transactions"},
                }
            },
            {"$project": {"_id": 0, "address": "$location", "transactions": 1}},
        ]

        return list(self.homes.aggregate(pipeline))


    # Working - needs to be in website
    def list_owners_with_most_expensive_homes_in_city(self, city):
        """List owners who own all the most expensive homes in a given city"""
        pipeline = [
            # Step 1: Join HOME collection with TRANSACTION to get home prices
            {
                "$lookup": {
                    "from": "TRANSACTIONS",
                    "localField": "_id",  # Assuming home _id is what TRANSACTION references
                    "foreignField": "home",  # Assuming 'home' in TRANSACTION refers to HOME _id
                    "as": "transactions",
                }
            },
            # Optional: If you want only the latest transaction for each home
            {
                "$addFields": {
                    "latest_transaction": {
                        "$arrayElemAt": ["$transactions", -1]
                    }  # Assuming the last transaction is the latest
                }
            },
            # Step 2: Filter by city
            {"$match": {"location.city": city}},
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
                    "owner_name": {
                        "$concat": ["$owner.first_name", " ", "$owner.last_name"]
                    },
                    "home_value": "$latest_transaction.price",
                    "location": 1,
                }
            },
        ]

        # Execute aggregation pipeline
        return list(self.homes.aggregate(pipeline))


    # Homes for sale already done on Transactions Page
    def find_home_for_sale(self, **params):
        """Find homes that up for sale in a given city that meet certain buyer choices such as number of bedrooms, baths, etc"""

        matches = {f"home_details.{k}": v for k, v in params}

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
                    "as": "home_details",
                }
            },
            {"$unwind": "$home_details"},  # Deconstruct the home_details array
            # Step 3: Filter homes based on the specified number of bedrooms and bathrooms
            {"$match": matches},
            # Project/format the output
            {
                "$project": {
                    "_id": 0,
                    "home_id": "$home",  # Show home id
                    "bedrooms": "$home_details.bed_rooms",
                    "bathrooms": "$home_details.bath_rooms",
                    "for_sale": {
                        "$ifNull": ["$seller", True]
                    },  # Indicate the home is for sale
                    "location": "$home_details.location",  # Assuming you store location info in the HOME collection
                    "price": "$price",  # Assuming price is in the TRANSACTION
                }
            },
        ]

        return list(self.transactions.aggregate(pipeline))
