from flask import Flask, Blueprint
from flask_restx import Api, Resource
from flask_mail import Mail
from application.scripts.AES import AESCipher
import os
import pymongo

import certifi
ca = certifi.where()

app = Flask(__name__)
blueprint = Blueprint('api', __name__, url_prefix='/api/')


api = Api(blueprint,default="Product",default_label="Retreive product/db stats", description="API allows to retrieve products' historical data and database statistics.",title="borabora-analyzer api")
app.register_blueprint(blueprint)
api.init_app(app,add_specs=False,debug=True)

# app.secret_key = os.environ.get("SESSION_COOKIE_PWD")


# app.config.update({
#     "SECRET_KEY":os.environ.get("SESSION_COOKIE_PWD"),
#     "SESSION_COOKIE_SECURE":True,
# })

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": os.environ.get("EMAIL_USERNAME"),
    "MAIL_PASSWORD": os.environ.get("EMAIL_APP_PASSWORD")
}

app.config.update(mail_settings)
server_mail = Mail(app)

#connecting to db
# DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
#               f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
#               'retryWrites=true&w=majority'
DATABASE_URL=f'mongodb+srv://{os.environ.get("DB_NAME_2")}:{os.environ.get("DB_PASSWORD_2")}'\
        '@cluster0.ichgboc.mongodb.net/?retryWrites=true&w=majority'
client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
mongo_db=client.db # assign database to mongo_db

AES = AESCipher(os.environ.get("USER_CALLBACK_PWD"))
    
from application import routes


