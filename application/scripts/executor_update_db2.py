from webcrawler import BarboraCrawler
from db_handler import MongoDatabase
import pymongo, os

import certifi
ca = certifi.where()

from dotenv import load_dotenv
load_dotenv()


def Main():
    #scrape barbora
    crawler = BarboraCrawler()
    crawler.analyze()
    
    crawler.outputDatabase()
    
    #upload database
    DATABASE_URL=f'mongodb+srv://{os.environ.get("DB_NAME_2")}:{os.environ.get("DB_PASSWORD_2")}'\
        '@cluster0.ichgboc.mongodb.net/?retryWrites=true&w=majority'
    client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    mongo_db=client.db
    mongoHandle = MongoDatabase(mongo_db)
    mongoHandle.update_day(crawler.database)
    mongoHandle.trim_db_submit(limit=int(os.environ.get("DB_PRODUCTS_DAY_LIMIT")))
    mongoHandle.clean_user_alerts()

if __name__ == "__main__":
    Main()

