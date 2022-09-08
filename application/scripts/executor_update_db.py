from webcrawler import BarboraCrawler
from mongodb import MongoDatabase
import pymongo, os

import certifi
ca = certifi.where()

from dotenv import load_dotenv
load_dotenv()


def Main():
    #scrape barbora
    crawler = BarboraCrawler()
    crawler.analyze()
    #upload database
    DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
              f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
              'retryWrites=true&w=majority'
    client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    mongo_db=client.db
    mongoHandle = MongoDatabase(mongo_db)
    mongoHandle.update(crawler.database)
    mongoHandle.checkForDuplicatesAndFix()
    mongoHandle.trim_to_limit()
    mongoHandle.clean_user_alerts()

if __name__ == "__main__":
    Main()

