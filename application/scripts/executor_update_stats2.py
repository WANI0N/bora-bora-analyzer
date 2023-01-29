from db_analyzer2 import DbAnalyzer
import pymongo, os

import certifi
ca = certifi.where()

from dotenv import load_dotenv
load_dotenv()


def Main():
    DATABASE_URL=f'mongodb+srv://{os.environ.get("DB_NAME_2")}:{os.environ.get("DB_PASSWORD_2")}'\
        '@cluster0.ichgboc.mongodb.net/?retryWrites=true&w=majority'
    client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    mongo_db=client.db
    #recalculate
    analyzer = DbAnalyzer(mongo_db)
    analyzer.analyze_and_push(True)


if __name__ == "__main__":
    Main()