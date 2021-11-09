from datetime import datetime, timedelta
import hashlib
class API_Limiter:
    def __init__(self):
        """checks IP of requestor and logs timestamps, declines requests if exceeded
        """
        self.apiLimits = {
            "default":{
                "endPoint":"api",
                "type":"ip",
                "timeUnit":"minute",
                "count":15
            },
            "specific":{
                "api/product-ids":{
                    "endPoint":"api/product-ids",
                    "type":"ip",
                    "timeUnit":"minute",
                    "count":1
                    },
                "api/addAlert":{
                    "endPoint":"api/addAlert",
                    "type":"ip",
                    "timeUnit":"minute",
                    "count":100
                },
                "api/submitAlerts":{
                    "endPoint":"api/submitAlerts",
                    "type":"ip",
                    "timeUnit":"minute",
                    "count":100
                },
            }
        }
        self.requests = {}

        self.loginAttemptLimit = 5 #per minute
        self.loginRequests = {}

    def submit(self,ipAddress,url,method,**kwargs):
        endPoint = self.getEndpoint(url)
        if (endPoint[0:3] != 'api'):
            # normal route
            return True
        limit = self.getLimit(endPoint,method)
        key = f"{ipAddress} - {limit['endPoint']}"
        return self.checkAccess('api',key,limit)
    
    def checkAccess(self,type,key,limit = None):
        if type == "api":
            targetHashMap = self.requests
            count = limit['count']
        elif type == "login":
            targetHashMap = self.loginRequests
            count = self.loginAttemptLimit
        else:
            raise('invalid checkAccess type')
        if key not in targetHashMap:
            targetHashMap[key] = []
        now = datetime.now()
        if len( targetHashMap[key] ) < count:
            timeStamp = now.strftime('%Y-%m-%d %H:%M:%S')
            targetHashMap[key].append( timeStamp )
            return True
        else:
            firstTime = datetime.strptime(targetHashMap[key][0],"%Y-%m-%d %H:%M:%S")
            if (firstTime > now-timedelta(minutes=1)):
                return False
            timeStamp = now.strftime('%Y-%m-%d %H:%M:%S')
            targetHashMap[key].pop(0)
            targetHashMap[key].append( timeStamp )
            return True


    def loginAttemptSubmit(self,ipAddress,email):
        """login limit agains brute force (hooked to both IP and email)

        Args:
            ipAddress (string): requestor IP
            email (string): any

        Returns:
            [boolean]: pass status (True=proceed|False=block)
        """
        key = email if email else ipAddress
        key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        return self.checkAccess('login',key)
        

    def getLimit(self,endPoint,method):
        if endPoint not in self.apiLimits['specific']:
            return self.apiLimits['default']
        else:
            return self.apiLimits['specific'][endPoint]
        

    def getEndpoint(self,url):
        #http://127.0.0.1:5000/api/product?brand_name=AROSO
        pop = True if '?' in url else False
        url = url.replace('?','/')
        arr = url.split('/')
        arr = arr[3::]
        if pop:
            arr.pop()
        # print("/".join(arr))
        return "/".join(arr)

if __name__ == "__main__":
    url = "http://127.0.0.1:5000/api/product?brand_name=AROSO"
    # limiter = Limiter()
    # limiter.getEndpoint(url)
    # endPoint = 'api/asd'
    # length = len('api')
    # print(endPoint)
    # print(endPoint[0:length])