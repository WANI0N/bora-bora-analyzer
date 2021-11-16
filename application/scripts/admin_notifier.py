from dotenv import load_dotenv
import os
import certifi
ca = certifi.where()
load_dotenv()
from datetime import datetime
import pymongo
import smtplib, ssl

class AdminNotifier:
    def __init__(self,db):
        self.db = db
        self.serverEmailAddress = os.environ.get("EMAIL_USERNAME")
        self.serverEmailPassword = os.environ.get("EMAIL_PASSWORD")
        self.userChangeNotification = False
        self.dbPullStatusNotification = False
    
    def execute(self):
        self.checkDbPullStatus()
        self.checkUserCountChange()
        self.updateDbStatusCollection()
        self.notify()
    
    def updateDbStatusCollection(self):
        content = dict({
            "userCount":self.db.user.count_documents({})
        })
        self.db.dbStatus.drop()
        self.db.dbStatus.insert_one( content )
    
    def checkUserCountChange(self):
        dbStatus = self.db.dbStatus.find_one({})        
        userCount = self.db.user.count_documents({})
        
        if (dbStatus["userCount"] == userCount):
            return
        self.userChangeNotification = {
            "from":dbStatus["userCount"],
            "to":userCount
        }
    
    def checkDbPullStatus(self):
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        ck = self.db.products.find_one({'history.0.date':current_date},{'id':1})
        if ck:
            return
        self.dbPullStatusNotification = current_date
    
    def notify(self):
        if not self.userChangeNotification and not self.dbPullStatusNotification:
            return
        adminUser = self.db.user.find_one({"admin":True},{"email":1})
        if not adminUser:
            return
        recipientEmail = adminUser['email']
        message = """\
        Activity Log [borabora-analyzer]
                    """
        message += "\n"
        if self.userChangeNotification: #dict
            message += f"User count changed from {self.userChangeNotification['from']} to {self.userChangeNotification['to']}"
            message += "\n\n"
        if self.dbPullStatusNotification: #string
            message += f"Database failed to update! Date - {self.dbPullStatusNotification}"
            message += "\n\n"
        
        message += f"Report Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(self.serverEmailAddress, self.serverEmailPassword)
            server.sendmail(self.serverEmailAddress, recipientEmail, message)

if __name__ == "__main__":
    DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
              f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
              'retryWrites=true&w=majority'
    client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    mongo_db=client.db
    notifier = AdminNotifier(mongo_db)
    notifier.execute()
    