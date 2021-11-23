# from flask import session
# from application import app
import certifi, json
ca = certifi.where()
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
load_dotenv()

from application.scripts.AES import AESCipher

class CookieHandler:
    def __init__(self):
        self.AES = AESCipher(os.environ.get("SESSION_COOKIE_PWD"))
        self.expirationPeriodHours = 12
    
    def createSession(self,cookie_id):
        cookies = {}
        expirationTime = datetime.now()+timedelta(hours=self.expirationPeriodHours)
        cookies["expiration"] = expirationTime.strftime("%Y-%m-%d %H:%M:%S")
        cookies["cookie_id"] = cookie_id
        return self.AES.encrypt( json.dumps(cookies) )
    
    def validateSession(self,cookieString):
        if not cookieString:
            return False
        try:
            cookies = json.loads( self.AES.decrypt(cookieString) )
        except:
            return False
        if "expiration" not in cookies:
            return False
        expirationTime = datetime.strptime(cookies["expiration"],"%Y-%m-%d %H:%M:%S")
        if expirationTime < datetime.now():
            return False
        return cookies["cookie_id"]
    
    def addCookie(self,cookieString,key,value):
        if not cookieString:
            cookies = {}
        else:
            try:
                cookies = json.loads( self.AES.decrypt(cookieString) )
            except:
                cookies = {}
        cookies[key] = value
        return self.AES.encrypt( json.dumps(cookies) )
    
    def validateCookie(self,cookieString,key,value=None):
        if not cookieString:
            return False
        try:
            cookies = json.loads( self.AES.decrypt(cookieString) )
        except:
            return False
        if key not in cookies:
            return False
        if value:
            if cookies[key] == value:
                return True
            return False
        return True
    
    def getCookies(self,cookieString):
        if not cookieString:
            return False
        try:
            return json.loads( self.AES.decrypt(cookieString) )
        except:
            return False
    
    def deleteCookie(self,cookieString,keyList):
        if not cookieString:
            return False
        try:
            cookies = json.loads( self.AES.decrypt(cookieString) )
        except:
            return False
        for key in keyList:
            if key in cookies:
                del cookies[key]
        return self.AES.encrypt( json.dumps(cookies) )
        
        