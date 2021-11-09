from flask_mail import Message
import certifi, json, hashlib, string, secrets
from datetime import datetime, timedelta
ca = certifi.where()
from dotenv import load_dotenv
import os
load_dotenv()

class User:
    def __init__(self,db,mail,AES):
        """handles user collection, email communication and token verificaiton

        Args:
            db (mongodb collection class): user route
            mail (email class): declared on app
            AES (encryption class): declared with static pwd
        """
        self.AES = AES
        self.mail = mail
        self.serverEmailAddress = os.environ.get("EMAIL_USERNAME")
        self.users = db
        self.alertLimit = 100
        self.saltLength = 10
        self.pendingValidationUserLimit = 5000
        self.serverUrl = os.environ.get("SERVER_ROOT_URL")
        
        self.alertKeys = dict({
            "productID":"string",
            "active":"boolean",
            "deactivate_after_alert":"boolean",
            "type":["availability","priceDrop","priceRaise","priceChange","unavailability"],
            "percentage":"integer",
        })

    def create(self,email,pwd):
        """creates new user, if maximum number of pending (unvalidated) users does not exceed maximum

        Args:
            email (string): no validation performed
            pwd (string): no validation performed

        Returns:
            [boolean]: success status
        """
        if self.users.find_one({"email":email},{"email":1}):
            return False
        if (self.users.count_documents({"validation_status":False}) > self.pendingValidationUserLimit):
            return False
        salt_pwd = self.getSalt()
        validation_end = datetime.now()+timedelta(days=2)
        validation_end = validation_end.strftime("%Y-%m-%d %H:%M:%S")
        userPush = dict({
            "email":email,
            "password":self.hash( pwd + salt_pwd ),
            "salt_pwd":salt_pwd,
            "id_cookie":self.hash( self.getSalt(20) ),
            "unsub_token":self.hash( self.getSalt(20) ),
            "validation_code":self.hash( self.getSalt(20) ),
            "validation_end":validation_end,
            "validation_status":False
        })
        self.users.insert_one(userPush)
        return True
    
    def cleanUp(self):
        """deletes users with expired validation period (used on server period reboot)
        """
        for user in self.users.find({"validation_status":False},{"id_cookie":1,"validation_end":1}):
            validation_end = datetime.strptime(user["validation_end"],"%Y-%m-%d %H:%M:%S")
            if ( validation_end > datetime.now() ):
                self.users.delete_one({"id_cookie":user["id_cookie"]})

    def logOut(self,cookie_id):
        """replaces user cookie_id (hence logout happens on multiple devices/browsers)

        Args:
            cookie_id (string): cookie
        """
        self.users.update_one({"id_cookie":cookie_id},
        {
            "$set":{
                "id_cookie":self.hash( self.getSalt(20) )
            }
        })

    def delete(self,cookie_id):
        """if valid user cookie_id provided, deletes user

        Args:
            cookie_id (string): cookie

        Returns:
            [boolean]: success status
        """
        user = self.users.find_one({"id_cookie":cookie_id},{"id_cookie":1})
        if not user:
            return False
        self.users.delete_one({"id_cookie":cookie_id})
        return True

    def sendPasswordResetEmail(self,email):
        """if email exists, sends pwd reset email to user with generated reset_code

        Args:
            email (string): 

        Returns:
            [boolean]: success status
        """
        user = self.users.find_one({"email":email},{"id_cookie":1})
        if not user:
            return

        reset_code = self.hash( self.getSalt(20) )
        expiration_timestamp = datetime.now()+timedelta(hours=24)
        expiration_timestamp = expiration_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        pwdReset = {
            "reset_code":reset_code,
            "expiration_timestamp":expiration_timestamp
        }
        self.users.update_one({"id_cookie":user["id_cookie"]},
        {
            "$set":{
                "pwdReset":pwdReset
            }
        })

        link = self.serverUrl + "/password-reset?reset_code=" + reset_code
        subject = "Password Reset [borabora-analyzer]"
        
        text = "Hello!\nPassword reset has been requested for your borabora-analyzer account. To set a new password, please click on this link:\n"
        text += link
        f = open('application/static/html/email_resetPassword.html','r')
        html = f.read().replace("BDHSUIAYCDISOIUHDAIUBDAIOSG", link)
        f.close()

        msg = Message(subject, sender = self.serverEmailAddress, recipients = [email])
        msg.body = text
        msg.html = html

        with open('application/static/html/img/logo-small.png', 'rb') as fp:
            msg.attach('logoSmall.jpg', 'image/jpg', fp.read(), 'inline', headers=[['Content-ID','<logoSmall>']])
        
        self.mail.send(msg)
        return True

    def verifyPasswordResetSubmit(self,reset_code):
        """checks validity and removes reset_code (if used, new must be generated)

        Args:
            reset_code ([string])

        Returns:
            False or user's cookie_id
        """
        user = self.users.find_one({ "pwdReset.reset_code": reset_code },{"pwdReset":1,"id_cookie":1})
        if not user:
            return False
        expiration = datetime.strptime(user['pwdReset']['expiration_timestamp'],"%Y-%m-%d %H:%M:%S")
        if (expiration < datetime.now()):
            return False
        self.users.update_one({"id_cookie":user["id_cookie"]},
        {
            "$unset":{
                "pwdReset":""
            }
        })
        return user["id_cookie"]

    def checkUnsubToken(self,unsubToken):
        """verifies if token exists

        Args:
            unsubToken ([string]): 

        Returns:
            [boolean]: success status
        """
        user = self.users.find_one({"unsub_token":unsubToken},{"id_cookie":1})
        if not user:
            return False
        return True

    def unsubscribeUser(self,unsubToken,deactivate,remove):
        """sets all user's alerts to off or removes them

        Args:
            unsubToken (string): validation code to identify user
            deactivate (boolean): 
            remove (boolean): if true ignores 'deactivate'

        Returns:
            [boolean]: success status
        """
        if remove:
            user = self.users.find_one({"unsub_token":unsubToken},{"id_cookie":1})
            if not user:
                return False
            self.users.update_one({"id_cookie":user["id_cookie"]},
            {
                "$unset":{
                    "alerts":""
                }
            })
            return True
        if deactivate:
            user = self.users.find_one({"unsub_token":unsubToken},{"id_cookie":1,"alerts":1})
            if not user:
                return False
            for alert in user["alerts"]:
                alert['active'] = False
            self.users.update_one({"id_cookie":user["id_cookie"]},
            {
                "$set":{
                    "alerts":user["alerts"]
                }
            })
            return True
        return False
        

    def setOneTimeToken(self,cookie_id,tokenType,**kwargs):
        """Sets enctypted json array string on user containing specific type (usage) and cookie_id to identify user

        Args:
            cookie_id (string): [description]
            tokenType (string): [description]

        Returns:
            token [string]: needed for js call to API to perform action
        """
        user = self.users.find_one({"id_cookie":cookie_id},{"id_cookie":1})
        if not user:
            return False
        
        token = [tokenType,cookie_id]
        if 'expiration_timestamp' in kwargs:
            token.append( kwargs['expiration_timestamp'] )
        token.append( self.getSalt(20) )
        token = self.AES.encrypt(json.dumps( token ))
        self.users.update_one({"id_cookie":user["id_cookie"]},{"$set":{"one_time_token":token}})
        
        return token

    def validateOneTimeToken(self,token,token_required_type,callBack = None):
        """Validate if token is saved on user and token is expected type

        Args:
            token (string): encrypted
            token_required_type (string): expected type
            callBack ([type], optional): [description]. Defaults to None.

        Returns:
            if valid:
                user object or specific key from user object
            else: False
        """
        token = self.AES.decrypt(token)
        arr = json.loads( token )
        # validated token type for required action
        if (token_required_type != arr[0]):
            return False
        # check if user exist, built user object return
        user = self.users.find_one({"id_cookie":arr[1]},{"alerts":0})
        if not user:
            return False
        
        # remove token on validation (or if expired)
        self.users.update_one({"id_cookie":user["id_cookie"]},
        {
            "$unset":{
                "one_time_token":""
            }
        })
        if (len(arr) == 4): # has expiration set
            timeStamp = datetime.strptime(arr[2],"%Y-%m-%d %H:%M:%S")
            if (timeStamp < datetime.now()):
                return False
        if not callBack:
            return user
        return user[callBack]

    def validateUserCookie(self,cookie_id = None):
        """checks if cookie_id exists in db

        Args:
            cookie_id (string, optional): cookie. Defaults to None.

        Returns:
            [boolean]: success status
        """
        if not cookie_id:
            return False
        if self.users.find_one({"id_cookie":cookie_id},{"_id":1}):
            return True
        return False
    
    def getUserCookie(self,email):
        """retreive cookie_id if user email exists

        Args:
            email (string): no validation

        Returns:
            cookie_id or False
        """
        user = self.users.find_one({"email":email},{"id_cookie":1})
        if not user:
            return False
        return user["id_cookie"]

    def getUserByCookie(self,id_cookie):
        """retreives user class (without alerts)

        Args:
            id_cookie (string): cookie

        Returns:
            False or user object
        """
        if id_cookie:
            user = self.users.find_one({"id_cookie":id_cookie},{"alerts":0})
        if user:
            return user
        return False

    def getUserByEmail(self,email):
        """retreives user class (without alerts)

        Args:
            email (string): no validation

        Returns:
            False or user object
        """
        user = self.users.find_one({"email":email},{"alerts":0})
        if user:
            return user
        return False

    def updatePassword(self,cookie_id,current_pwd,new_pwd):
        """verifies if user exists and current pwd matches, then sets new pwd and cookie

        Args:
            cookie_id (string): cookie
            current_pwd (string): old pwd
            new_pwd (string): new pwd

        Returns:
            object: success:True/False
            if False: reason: string
        """
        user = self.users.find_one({"id_cookie":cookie_id},{"salt_pwd":1,"password":1})
        if not user:
            return {
                "success":False,
                "reason":"User not found."
            }
        if (self.hash(current_pwd + user["salt_pwd"]) != user["password"]):
            return {
                "success":False,
                "reason":"Incorrect current password."
            }
        # setting new cookie
        self.users.update_one({"id_cookie":cookie_id},
        {
            "$set":{
                "id_cookie":self.hash( self.getSalt(20) ),
                "password":self.hash( new_pwd + user["salt_pwd"] ),
            }
        })
        return {"success":True}

    def resetPassword(self,token,new_pwd):
        """Sets new password and new cookie_id

        Args:
            token (string): one time temporary validation token (includes user identifier)
            new_pwd (string): no validation performed

        Returns:
            [boolean]: success status
        """
        user = self.validateOneTimeToken(token,"submitNewPassword")
        if not user:
            return False
        
        self.users.update_one({"id_cookie":user['id_cookie']},
        {
            "$set":{
                "id_cookie":self.hash( self.getSalt(20) ),
                "password":self.hash( new_pwd + user["salt_pwd"] ),
            }
        })
        return True

    def validateUser(self,email,pwd):
        """check if login information is correct

        Args:
            email (string)
            pwd (string)

        Returns:
            [boolean]: success status
        """
        user = self.users.find_one({"email":email},{"email":1,"salt_pwd":1,"password":1})
        if not user:
            return False
        if (self.hash(pwd + user["salt_pwd"]) != user["password"]):
            return False
        return True
    
    def validateUserEmail(self,validation_code):
        """if success, sets email validation to True and removes validation code

        Args:
            validation_code (string)

        Returns:
            [boolean]: success status
        """
        user = self.users.find_one({"validation_code":validation_code},{"validation_code":1,"validation_end":1})
        if not user:
            return False
        validationTime = datetime.strptime(user["validation_end"],"%Y-%m-%d %H:%M:%S")
        registrationTime = validationTime-timedelta(days=2)
        self.users.update_one({"validation_code":validation_code},
        {
            "$unset":{
                "validation_code":"",
                "validation_end":""
            },
            "$set":{
                "registration_time":registrationTime.strftime("%Y-%m-%d %H:%M:%S"),
                "validation_status":True
            }
        })
        return True

    def sendValidationEmail(self,email):
        """send email validation if user's email exists + email not yet validated

        Args:
            email (string)

        Returns:
            [boolean]: success status
        """
        user = self.users.find_one({"email":email},{"alerts":0})
        if not user:
            return False

        if user["validation_status"]:
            return False
        link = self.serverUrl + "/email-validation/" + user["validation_code"]
        subject = "Email validation [borabora-analyzer]"
        
        text = "Hello!\nPlease click on the following link to validated your email with borabora-analyzer:\n"
        text += link
        f = open('application/static/html/email_validation.html','r')
        html = f.read().replace("BDHSUIAYCDISOIUHDAIUBDAIOSG", link)
        f.close()

        msg = Message(subject, sender = self.serverEmailAddress, recipients = [user["email"]])
        msg.body = text
        msg.html = html

        with open('application/static/html/img/logo-small.png', 'rb') as fp:
            msg.attach('logoSmall.jpg', 'image/jpg', fp.read(), 'inline', headers=[['Content-ID','<logoSmall>']])
        
        self.mail.send(msg)
        
        return True

    def addAlert(self,cookie_id,productId,innitial_state):
        """adds alert to user, if max number of alerts not exceeded

        Args:
            cookie_id (string): cookie
            productId (string): no verification done
            innitial_state (boolean): innitial alert type is set to available or unavailable

        Returns:
            [boolean]: success status
        """
        user = self.users.find_one({"id_cookie":cookie_id},{"alerts":1})
        if not user:
            return False
        alerts = [] if 'alerts' not in user else user['alerts']
        if (len(alerts) >= self.alertLimit):
            return False
        alerts.append({
            "productID":productId,
            "active":True,
            "deactivate_after_alert":True,
            "type":"availability" if innitial_state else "unavailability",
            "percentage":0
        })
        self.users.update_one({"id_cookie":cookie_id},{"$set":{"alerts":alerts}})
        return True

    def getAlerts(self,cookie_id):
        """retreive user alerts

        Args:
            cookie_id (string): 

        Returns:
            alerts list (can be empty) or False is user not found
        """
        user = self.users.find_one({"id_cookie":cookie_id},{"alerts":1})
        if not user:
            return False
        alerts = [] if 'alerts' not in user else user['alerts']
        return alerts

    def updateAlerts(self,cookie_id,alerts):
        """updates user's alerts

        Args:
            cookie_id (string)
            alerts (list): final list, verification performed

        Returns:
            [boolean]: success status
        """
        if (len(alerts) >= self.alertLimit):
            return False
        user = self.users.find_one({"id_cookie":cookie_id},{"id_cookie":1})
        if not user:
            return False
        for item in alerts:
            if (len(item) != len(self.alertKeys)):
                return False
            for k, v in item.items():
                if k not in self.alertKeys:
                    return False
                if (self.alertKeys[k] == "string"):
                    if not isinstance(v,str):
                        return False
                if (self.alertKeys[k] == "boolean"):
                    if not isinstance(v,bool):
                        return False
                if (self.alertKeys[k] == "integer"):
                    if not isinstance(v,int):
                        return False
                if isinstance(self.alertKeys[k],list):
                    if v not in self.alertKeys[k]:
                        return False
        self.users.update_one({"id_cookie":cookie_id},{"$set":{"alerts":alerts}})
        return True

    def hash(self,string):
        """sha256 for string

        Args:
            string (string): any

        Returns:
            hash string
        """
        return hashlib.sha256(string.encode('utf-8')).hexdigest()
    def getSalt(self,length = None):
        """generates random string (salt)

        Args:
            length (integer, optional): Default specified in contructor. Defaults to None.

        Returns:
            random string
        """
        if not length:
            length = self.saltLength
        return str(
            ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(length))  
        )


if __name__ == "__main__":
    pass
    