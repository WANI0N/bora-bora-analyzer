from db_analyzer import DbAnalyzer
from webcrawler import BarboraCrawler
# from TEST_mongodb import MongoDatabase
from mongodb import MongoDatabase
import pymongo, os

import certifi
ca = certifi.where()

from dotenv import load_dotenv
load_dotenv()

# import json
# from functions import *

if __name__ == "__main__":
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
    
    # from datetime import datetime
    # import json
    # now = datetime.now()
    # current_date = now.strftime("%Y-%m-%d")
    # f = open(current_date + '.json','a') #1203075,867412
    # f.write( json.dumps( crawler.database, indent='\t' ) )
    # f.close()

    #recalculate
    analyzer = DbAnalyzer(mongo_db)
    analyzer.executeAndDiscard(True)
    
