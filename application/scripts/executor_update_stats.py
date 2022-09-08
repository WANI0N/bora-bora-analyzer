from db_analyzer import DbAnalyzer
import pymongo, os

import certifi
ca = certifi.where()

from dotenv import load_dotenv
load_dotenv()


def Main():
    DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
              f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
              'retryWrites=true&w=majority'
    client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    mongo_db=client.db
    #recalculate
    analyzer = DbAnalyzer(mongo_db)
    analyzer.executeAndDiscard(True)


if __name__ == "__main__":
    Main()