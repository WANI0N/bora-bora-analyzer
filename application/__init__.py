from flask import Flask, Blueprint
from flask_restx import Api, Resource
import os
import pymongo

import certifi
ca = certifi.where()

app = Flask(__name__)
blueprint = Blueprint('api', __name__, url_prefix='/api/')


api = Api(blueprint, description="API allows to retrieve products' historical data and database statistics.",title="borabora-analyzer api")
app.register_blueprint(blueprint)
api.init_app(app,add_specs=False,debug=True)
# app.config.update(
#     TESTING=True,
#     TEMPLATES_AUTO_RELOAD = True
# )
#connecting to db
DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
              f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
              'retryWrites=true&w=majority'

client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
mongo_db=client.db # assign database to mongo_db
#mongo_db.products.drop() # clear the collection
# mongo_db.products.insert_one(final_db)
# mongo_db.products.insert_many(file_data)

    
from application import routes


