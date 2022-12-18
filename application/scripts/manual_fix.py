import sys
import pymongo, os
from mongodb import MongoDatabase

import certifi
ca = certifi.where()

from dotenv import load_dotenv
load_dotenv()

def Main():
    target_date = sys.argv[1]
    if len(target_date) != 10:
        print(f"invalid date: {target_date}")
        return
    if target_date[4] != "-" or target_date[7] != "-":
        print(f"invalid date: {target_date}")
        return
    DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
              f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
              'retryWrites=true&w=majority'
    client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    mongo_db=client.db
    mongoHandle = MongoDatabase(mongo_db)
    mongoHandle.drop_date_fm_db_threaded_caller(target_date)
    

if __name__ == "__main__":
    Main()
    