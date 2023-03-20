import pymongo, os, json

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from email.mime.image import MIMEImage
import certifi
ca = certifi.where()
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timedelta

from functions import get_product_url_link, convert_history_to_old_format

class SendAlerts:
    def __init__(self,db):
        self.db = db
        self.sender_email = os.environ.get("EMAIL_USERNAME")
        # self.password = os.environ.get("EMAIL_PASSWORD")
        self.password = os.environ.get("EMAIL_APP_PASSWORD")
        
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        yesterday_date = datetime.now()-timedelta(days=1)
        self.yesterday_date = yesterday_date.strftime("%Y-%m-%d")
        
        self.user_change_notification = False
        self.db_pull_status_notification = False

    def execute(self):
        self.login_smtpServer()
        self.check_db_pull_status()
        self.check_user_count_change()
        self.update_db_status_collection()
        self.admin_notify()
        if not self.db_pull_status_notification: #no db error
            self.get_user_alerts()
            for recipient in self.notification_data:
                self.send_alerts_to_user(recipient['email'],recipient['unsubToken'],recipient['alerts'])
        self.smtpServer.quit()

    def login_smtpServer(self):
        context = ssl.create_default_context()
        self.smtpServer = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context)
        self.smtpServer.login(self.sender_email, self.password)
        

    def get_user_alerts(self):
        self.notification_data = []
        for user in self.db.user.find({},{"alerts":1,"email":1,"id_cookie":1,"unsub_token":1}):
            user_alert_list = []
            if 'alerts' not in user:
                continue
            alert_ids = [alert['productID'] for alert in user['alerts']]
            products = {}
            for prod in self.db.products.find({"id": {"$in": alert_ids}}, {"id": 1, "history": 1,"image": 1,"title": 1}):
                products[prod['id']] = prod
            for i, alert in enumerate(user['alerts']):
                if alert['productID'] not in products:
                    continue
                product = products[alert['productID']]
                product['history'] = convert_history_to_old_format(product['history'])
                status = self.determine_alert(product,alert)
                # print(status)
                if isinstance(status, str):
                    user_alert_list.append({
                        "title": product['title'],
                        "img": product['image'],
                        "description": status,
                        "bora_link": f"https://borabora-analyzer.herokuapp.com/analyze?id={alert['productID']}",
                        "barb_link": get_product_url_link(product['title']),
                        "deactivation": alert['deactivate_after_alert']
                    })
                    if alert['deactivate_after_alert']:
                        self.db.user.update_one({"id_cookie": user['id_cookie']},{
                            "$set":{
                                f"alerts.{i}.active": False
                            }
                        })
                
            if user_alert_list:
                self.notification_data.append({
                    "email":user['email'],
                    "unsubToken":user["unsub_token"],
                    "alerts":user_alert_list
                })

    def determine_alert(self,product,alert):
        if not alert['active']:
            return False
        if alert['type'] == 'unavailability':
            if (self.yesterday_date == datetime.strptime(product['history'][1]['date'],"%Y-%m-%d")):
                if product['history'][1]['active']:
                    if not product['history'][0]['active']:
                        return "Product has become unavailable."
                        
        if (self.current_date != product['history'][0]['date']):
            return False
        if not product['history'][0]['active']:
            return False
        if alert['type'] == 'availability':
            return "Product is available."
        
        if product['history'][0]['price'] == product['history'][1]['price']:
            return False
        
        price_change_percent = product['history'][0]['price']/product['history'][1]['price']*100-100
        percent_rounded = round(abs(price_change_percent),2)
        if alert['type'] == 'priceDrop':
            if (price_change_percent >= 0): #must be negative
                return False
            if (abs(price_change_percent) >= alert['percentage']):
                description = f"Price has dropped by {percent_rounded}% "
                description += f"(€{product['history'][1]['price']} => €{product['history'][0]['price']})"
                return description
        
        if alert['type'] == 'priceRaise':
            if (price_change_percent <= 0): #must be positive
                return False
            if (abs(price_change_percent) >= alert['percentage']):
                description = f"Price was raised by {percent_rounded}% "
                description += f"(€{product['history'][1]['price']} => €{product['history'][0]['price']})"
                return description
        
        if alert['type'] == 'priceChange':
            if (abs(price_change_percent) >= alert['percentage']):
                description = f"Price has changed by {percent_rounded}% "
                description += f"(€{product['history'][1]['price']} => €{product['history'][0]['price']})"
                return description

        return False

        

    def send_alerts_to_user(self,receiver_email,unsubToken,data):
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Product Alerts [borabora-analyzer]"
        message["From"] = self.sender_email
        message["To"] = receiver_email
        message.set_charset('utf8')

        text = "Unfortunatelly this email is only available in html or json:\n"
        jsonString = json.dumps( data,indent='\t' )
        text += f"{jsonString}"
        
        f = open('application/static/html/email_productAlert.html','r')
        html = f.read()
        f.close()

        f = open('application/static/html/product-line.html','r')
        productLineHtml = f.read()
        f.close()

        insertHtml = []
        for item in data:
            content = productLineHtml
            content = content.replace("REPLACE_TITLE", item['title'])
            content = content.replace("REPLACE_IMGLINK", item['img'])
            content = content.replace("REPLACE_DESCRIPTION", item['description'])
            content = content.replace("REPLACE_BARBLINK", item['barb_link'])
            content = content.replace("REPLACE_BORALINK", item['bora_link'])
            content = content.replace("REPLACE_DEACTIVATEMSG", 'This alert has been automatically deactivated.' if item['deactivation'] else 'This alert is continuously active.' )
            insertHtml.append( content )

        html = html.replace( 'BLOCK_CONTENT','\n'.join(insertHtml) )
        html = html.replace("REPLACE_UNSUBTOKEN", unsubToken)
        
        part1 = MIMEText(text.encode('utf-8'), "plain",'UTF-8')
        part2 = MIMEText(html.encode('utf-8'), "html",'UTF-8')

        message.attach(part1)
        message.attach(part2)

        b = message.as_string().encode('utf-8')
        self.smtpServer.sendmail(self.sender_email,receiver_email, b)
        
    def update_db_status_collection(self):
        content = dict({
            "userCount":self.db.user.count_documents({})
        })
        self.db.dbStatus.drop()
        self.db.dbStatus.insert_one( content )
    
    def check_user_count_change(self):
        dbStatus = self.db.dbStatus.find_one({})        
        userCount = self.db.user.count_documents({})
        
        if (dbStatus["userCount"] == userCount):
            return
        self.user_change_notification = {
            "from":dbStatus["userCount"],
            "to":userCount
        }
    
    def check_db_pull_status(self):
        if not self.db.products.find_one({'history.0.end-date': self.current_date},{'id':1}):
            self.db_pull_status_notification = True
            return
        if not self.db.dbStatsDataFinal.find_one({'date': self.current_date}, {'date': 1}):
            self.db_pull_status_notification = True
    
    def admin_notify(self):
        if not self.user_change_notification and not self.db_pull_status_notification:
            return
        adminUser = self.db.user.find_one({"admin":True},{"email":1})
        if not adminUser:
            return
        recipientEmail = adminUser['email']
        message = """\
        Activity Log [borabora-analyzer]
                    """
        message += "\n"
        if self.user_change_notification: #dict
            message += f"User count changed from {self.user_change_notification['from']} to {self.user_change_notification['to']}"
            message += "\n\n"
        if self.db_pull_status_notification: #string
            message += f"Database failed to update! Date - {self.current_date}"
            message += "\n\n"
        
        message += f"Report Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.smtpServer.sendmail(self.sender_email, recipientEmail, message)
    
if __name__ == '__main__':
    DATABASE_URL=f'mongodb+srv://{os.environ.get("DB_NAME_2")}:{os.environ.get("DB_PASSWORD_2")}'\
        '@cluster0.ichgboc.mongodb.net/?retryWrites=true&w=majority'
    client=pymongo.MongoClient(DATABASE_URL, tlsCAFile=ca) # establish connection with database
    mongo_db=client.db
    alerts = SendAlerts(mongo_db)
    alerts.execute()
    