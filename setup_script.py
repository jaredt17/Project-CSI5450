from enum import Enum
from typing import List

from pymongo import MongoClient
from bson import ObjectId

DB = "realmi"

class TABLES(str, Enum):

    homes = "homes"
    locations = "locations"
    appliances = "appliances"
    agents = "agents"
    owners = "owners"
    transactions = "transactions"
    companies = "companies"


class HomeType(str, Enum):

    mansion = "Mansion"
    apartment = "Apartment"
    townhome = "Townhome"
    condo = "Condo"

    def decide(floor_space: int, floors: int, bed_rooms: int, bath_rooms: float, land_size: int) -> str:
        if floor_space >= 6000 and land_size > 2:
            return HomeType.mansion
        
        if floors > 1 and bed_rooms > 1:
            return HomeType.townhome
        
        if floors == 1:
            return HomeType.apartment


class HOME(str, Enum):

    floor_space = "FloorSpace"
    floors = "Floors"
    bed_rooms = "BedRooms"
    bath_rooms = "BathRooms"
    land_size = "LandSize"
    year_constructed = "YearConstructed"
    home_type = "HomeType"
    appliances = "Appliances"
    owner_id = "OwnerId"
    location_id = "LocationId"

    def new(floor_space: int, floors: int, bed_rooms: float, bath_rooms: float, land_size: float, year_constructed: int, appliances: List[ObjectId], owner: ObjectId = None):
        return {
            HOME.floor_space: floor_space,
            HOME.floors: floors,
            HOME.bed_rooms: bed_rooms,
            HOME.bath_rooms: bath_rooms,
            HOME.land_size: land_size,
            HOME.year_constructed: year_constructed,
            HOME.home_type: HomeType.decide(floor_space, floors, bed_rooms, bath_rooms, land_size),
            HOME.appliances: appliances,
            HOME.owner_id: owner
        }


class LOCATION(str, Enum):

    street_number = "StreetNumber"
    unit_number = "UnitNumber"
    street = "Street"
    city = "City"
    zip = "Zip"
    state = "State"
    county = "County"
    country = "Country"


class APPLIANCE(str, Enum):

    name = "Name"
    model = "Model"
    year = "Year"
    make = "Make"
    price = "Price"


class AGENT(str, Enum):

    first_name = "FirstName"
    last_name = "LastName"
    companies = "Companies"
    sales = "Sales"
    

class OWNER(str, Enum):

    first_name = "FirstName"
    last_name = "LastName"
    ssn = "SSN"
    no_dependents = "NoDependents"
    income = "Income"
    age = "Age"
    profession = "Profession"


class TRANSACTION(str, Enum):

    owner_id = "OwnerId"
    agent_id = "AgentId"
    company_id = "CompanyId"
    location_id = "LocationId"
    home_id = "HomeId"
    date = "Date"
    price = "Price"


class COMPANY(str, Enum):

    name = "Name"
    commission = "Commission"
    street_number = "StreetNumber"
    unit_number = "UnitNumber"
    street = "Street"
    city = "City"
    zip = "Zip"
    state = "State"


def setup():

    cl = MongoClient()

    cl.drop_database(DB)

    realmi = cl[DB]
    
    for k in TABLES.__dict__.keys():
        realmi.create_collection(k)

    

def main():
    setup()


if __name__ == "__main__":
    main()