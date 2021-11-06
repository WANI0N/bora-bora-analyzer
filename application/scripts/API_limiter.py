from datetime import datetime, timedelta
class API_Limiter:
    def __init__(self):
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

    def submit(self,ipAddress,url,method,**kwargs):
        endPoint = self.getEndpoint(url)
        if (endPoint[0:3] != 'api'):
            # normal route
            return True
        limit = self.getLimit(endPoint,method)
        key = f"{ipAddress} - {limit['endPoint']}"
        if key not in self.requests:
            self.requests[key] = []
        now = datetime.now()
        if len( self.requests[key] ) < limit['count']:
            timeStamp = now.strftime('%Y-%m-%d %H:%M:%S')
            self.requests[key].append( timeStamp )
            return True
        else:
            firstTime = datetime.strptime(self.requests[key][0],"%Y-%m-%d %H:%M:%S")
            if (firstTime > now-timedelta(minutes=1)):
                return False
            timeStamp = now.strftime('%Y-%m-%d %H:%M:%S')
            self.requests[key].pop(0)
            self.requests[key].append( timeStamp )
            return True
        

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