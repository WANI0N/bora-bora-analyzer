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

from functions import getProductUrlLink

from admin_notifier import AdminNotifier


class SendAlerts:
    def __init__(self,db):
        self.db = db
        self.sender_email = os.environ.get("EMAIL_USERNAME")
        self.password = os.environ.get("EMAIL_PASSWORD")
        
        self.login_smtpServer()

        self.currentDate = datetime.now().strftime("%Y-%m-%d")
        yesterdayDate = datetime.now()-timedelta(days=1)
        self.yesterdayDate = yesterdayDate.strftime("%Y-%m-%d")

    def execute(self):
        self.getUserAlerts()
        # print( self.notificationData )
        for recipient in self.notificationData:
            self.sendAlertsToUser(recipient['email'],recipient['unsubToken'],recipient['alerts'])

    def login_smtpServer(self):
        context = ssl.create_default_context()
        self.smtpServer = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context)
        self.smtpServer.login(self.sender_email, self.password)
        

    def getUserAlerts(self):
        self.notificationData = []
        for user in self.db.user.find({},{"alerts":1,"email":1,"id_cookie":1,"unsub_token":1}):
            userAlertList = []
            i = 0
            for alert in user['alerts']:
                product = self.db.products.find_one({"id":alert['productID']},{"history":1,"image":1,"title":1})
                status = self.determineAlert(product,alert)
                # print(status)
                if isinstance(status,str):
                    userAlertList.append({
                        "title":product['title'],
                        "img":product['image'],
                        "description":status,
                        "bora_link":f"https://borabora-analyzer.herokuapp.com/analyze?id={alert['productID']}",
                        "barb_link":getProductUrlLink(product['title']),
                        "deactivation":alert['deactivate_after_alert']
                    })
                    if alert['deactivate_after_alert']:
                        self.db.user.update_one({"id_cookie":user['id_cookie']},{
                            "$set":{
                                f"alerts.{i}.active":False
                            }
                        })
                i += 1
            if userAlertList:
                self.notificationData.append({
                    "email":user['email'],
                    "unsubToken":user["unsub_token"],
                    "alerts":userAlertList
                })

    def determineAlert(self,product,alert):
        if not alert['active']:
            return False
        if alert['type'] == 'unavailability':
            if (self.yesterdayDate == datetime.strptime(product['history'][1]['date'],"%Y-%m-%d")):
                if product['history'][1]['active']:
                    if not product['history'][0]['active']:
                        return "Product has become unavailable."
                        
        if (self.currentDate != product['history'][0]['date']):
            return False
        if not product['history'][0]['active']:
            return False
        if alert['type'] == 'availability':
            return "Product is available."
        
        if product['history'][0]['price'] == product['history'][1]['price']:
            return False
        
        priceChangePerCent = product['history'][0]['price']/product['history'][1]['price']*100-100
        perCentRounded = round(abs(priceChangePerCent),2)
        if alert['type'] == 'priceDrop':
            if (priceChangePerCent >= 0): #must be negative
                return False
            if (abs(priceChangePerCent) >= alert['percentage']):
                description = f"Price has dropped by {perCentRounded}% "
                description += f"(€{product['history'][1]['price']} => €{product['history'][0]['price']})"
                return description
        
        if alert['type'] == 'priceRaise':
            if (priceChangePerCent <= 0): #must be positive
                return False
            if (abs(priceChangePerCent) >= alert['percentage']):
                description = f"Price was raised by {perCentRounded}% "
                description += f"(€{product['history'][1]['price']} => €{product['history'][0]['price']})"
                return description
        
        if alert['type'] == 'priceChange':
            if (abs(priceChangePerCent) >= alert['percentage']):
                description = f"Price has changed by {perCentRounded}% "
                description += f"(€{product['history'][1]['price']} => €{product['history'][0]['price']})"
                return description

        return False

        

    def sendAlertsToUser(self,receiver_email,unsubToken,data):
        
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
        # if os.path.exists( 'finalEmail.html' ):
        #     os.remove( 'finalEmail.html' )
        # f = open('finalEmail.html','a',encoding='utf-8')
        # f.write( html )
        # f.close()
        
        # fp = open('application/static/html/img/logo-small.png', 'rb')
        # msgImage = MIMEImage(fp.read())
        # fp.close()
        # msgImage.add_header('Content-ID', '<logoSmall>')
        # message.attach(msgImage)

        # part1 = MIMEText(text, "plain")
        # part2 = MIMEText(html, "html")
        part1 = MIMEText(text.encode('utf-8'), "plain",'UTF-8')
        part2 = MIMEText(html.encode('utf-8'), "html",'UTF-8')

        message.attach(part1)
        message.attach(part2)

        b = message.as_string().encode('utf-8')
        self.smtpServer.sendmail(self.sender_email,receiver_email, b)
        # self.smtpServer.sendmail(self.sender_email,receiver_email, message.as_string())
        self.smtpServer.quit()


        
if __name__ == '__main__':
    DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
              f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
              'retryWrites=true&w=majority'
    client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    mongo_db=client.db
    alerts = SendAlerts(mongo_db)
    alerts.execute()
    
    notifier = AdminNotifier(mongo_db)
    notifier.execute()