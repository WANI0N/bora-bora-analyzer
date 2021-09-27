from flask import Flask, Blueprint
from flask_restx import Api
import os
import pymongo
from application.crawler.webcrawler import BarboraCrawler
# from datetime import datetime
app = Flask(__name__)
blueprint = Blueprint('api', __name__, url_prefix='/api/')
api = Api(blueprint)
app.register_blueprint(blueprint)
api.init_app(app,add_specs=False)

#connecting to db
DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
              f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
              'retryWrites=true&w=majority'

client=pymongo.MongoClient(DATABASE_URL) # establish connection with database
mongo_db=client.db # assign database to mongo_db
#mongo_db.products.drop() # clear the collection
# mongo_db.products.insert_one(final_db)
# mongo_db.products.insert_many(file_data)

## code runs only once in dev env
# if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
if True:
    # disable_onLoad = True
    disable_onLoad = False
    
from application import routes


