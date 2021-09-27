from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import threading
import json
import time
import os
import pymongo
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bson.json_util import dumps, loads
import os.path
import math

load_dotenv()

class BarboraCrawler:
    def __init__(self):
        self.baseUrl = 'https://pagrindinis.barbora.lt'
        self.topLinks = list()
        self.childLinks = list()
        self.productLinks = list()
        self.needleKeys = [
            # 'id','title','category_name_full_path','brand_name','price','image','comparative_unit','comparative_unit_price'
            'id','title','category_name_full_path','brand_name','image','comparative_unit','history'
        ]
        self.historyObjKeys = [
            'price','comparative_unit_price','date','active'
        ]
        self.database = []
    
    def urlToSoup(self,url = None):
        targetUrl = self.baseUrl
        if url:
            targetUrl = targetUrl + url
        try:
            page = urlopen(targetUrl)
        except HTTPError as err:
            print(err)
            raise
        except URLError as err:
            print(err)
            raise
        except:
            print('Unexpected error')
            raise
        return BeautifulSoup(page, 'html.parser')
    
    def analyze(self):
        self.getTopLinks()
        # self.getProductsFromPage('/mesa-zuvys-ir-kulinarija?page=16')

        self.getProductsFromTopLinks()
        #self.getChildLinks()
        #self.getProducts()
    
    def getProductsFromTopLinks(self):
        threads = list()
        for topLink in self.topLinks:
            t = threading.Thread(target=self.exportTopLink, args=[topLink])
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()
        
        ## removing keys out of target needle, trim id, add date
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        i = 0
        for item in self.database:
            self.database[i]["history"] = [{
                'price':item['price'],
                'comparative_unit_price':item['comparative_unit_price'],
                'date':current_date,
                'active':item['active'],
            }]
            self.database[i] = { key: item[key] for key in self.needleKeys }
            self.database[i]["id"] = self.database[i]["id"].lstrip("0")
            i += 1

    def exportTopLink(self,topLink):
        i = 1
        threads = list()
        for i in range(1,1000):
            respose = self.getProductsFromPage(topLink + "?page=" + str(i))
            if not respose:
                break
            i += 1

    def getProductsFromPage(self,childLink):
        print('extracting... ' + childLink)
        soup = self.urlToSoup(childLink)
        valid = False
        for div in soup.select('div[class*="b-product--wrap clearfix b-product--js-hook"]'):
            string = div.get('data-b-for-cart')
            string = string.replace('&quot;',"\"")
            obj = json.loads(string)
            if 'b-product-outofstock' in div['class']:
                obj['active'] = False
            else:
                obj['active'] = True
            self.database.append(obj)
            valid = True
        return valid

    def getTopLinks(self):
        # extracts top category product links from main page
        soup = self.urlToSoup()
        for container in soup.find_all('li', "b-categories-root-category"):
            for link in container.find_all('a'):
                self.topLinks.append( link.get('href') )
    
    def outputDatabase(self, format='json'):
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d") # - %H-%M-%S")
        if os.path.isfile(current_date + ".json"):
            os.remove(current_date + ".json")
        f = open(current_date + ".json","a")
        f.write( json.dumps(self.database,indent='\t') )
        f.close()




class MongoDatabase:
    def __init__(self):
        DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
              f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
              'retryWrites=true&w=majority'
        client=pymongo.MongoClient(DATABASE_URL) # establish connection with database
        self.db = client.db
        self.dbIds = list()
        for _id in self.db.products.find({},{"id":1}).distinct('id'):
            self.dbIds.append(_id)

    def update(self,uploadDB):
        if not isinstance(uploadDB,list):
            print('invalid uploadDB')
            return
        if 'date' not in uploadDB[0]['history'][0]:
            print('invalid uploadDB; missing history')
            return
        
        ck = self.db.products.find_one({'history.0.date':uploadDB[0]['history'][0]['date']},{'id':1})
        if ck:
            print(f"Server database already contains data of {uploadDB[0]['history'][0]['date']}")
            return
        
        threadCount = 20
        threadPayload = math.floor(len(uploadDB)/threadCount)
        padding = len(uploadDB) % threadPayload
        # print(len(uploadDB))
        # print( len(uploadDB)/threadCount )
        # print(threadPayload)
        # print(padding)
        
        threads = []
        for i in range(threadCount):
            startIndex = i*threadPayload
            endIndex = startIndex+threadPayload
            if (i == threadCount-1):
                endIndex += padding
            t = threading.Thread(target=self.executeUploadThread, args=[ uploadDB[startIndex:endIndex] ])
            t.start()
            print("thread started-> " + str(startIndex) + "-" + str(endIndex))
            threads.append(t)

        i = 0
        for thread in threads:
            print("thread #" + str(i) + " finished")
            thread.join()
            i += 1
        
        ##patching
        hashMap = dict()
        i = 0
        for item in uploadDB:
            hashMap[ item['id'] ] = i
            i += 1
        missingIds = list()
        
        # now = datetime.now()
        # current_date = now.strftime("%Y-%m-%d")
        for item in self.db.products.find({ "history.0.date": { "$ne": uploadDB[0]['history'][0]['date'] } },{'id':1}):
            if item['id'] in hashMap:
                missingIds.append(item['id'])
        for _id in missingIds:
            print("post patching..." + str(_id))
            self.db.products.update_one({'id':_id},{"$push":{"history":{
                "$each":[      uploadDB[   hashMap[ _id ]   ]['history'][0]     ],
                "$position":0
            }},"$set": { "image": uploadDB[   hashMap[ _id ]   ]['image'] }})
            
        # print(missingIds)
        print('done')

    def executeUploadThread(self,workLoad):
        for item in workLoad:
            if item['id'] in self.dbIds:
                self.db.products.update_one({'id':item['id']},{"$push":{"history":{
                    "$each":[      item['history'][0]      ],
                    "$position":0
                }},"$set": { "image": item['image'] }})
            else:
                self.db.products.insert_one( item )















#updating db if current date not present, manual for now
if __name__ == "__main__":
    
    crawler = BarboraCrawler()
    crawler.analyze()
    crawler.outputDatabase()

    
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    f = open(current_date + '.json','r') #1203075,867412
    string = f.read()
    data = json.loads( string )
    mongoHandle = MongoDatabase()
    mongoHandle.update(data)
    

    # DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
    #           f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
    #           'retryWrites=true&w=majority'
    # client=pymongo.MongoClient(DATABASE_URL) # establish connection with database
    # mongo_db=client.db
    

    
    # now = datetime.now()
    # current_date = now.strftime("%Y-%m-%d")
    # # mongo_db.pushToTest.drop()
    # ck = mongo_db.products.find_one({'history.0.date':current_date},{'id':1})
    # # print(ck)
    # if ck:
    #     print('update not needed')
    #     pass
    # else:
    #     print('update needed')
    #     userInput = input("Execute upload? Y/N: ")
    #     if (userInput == "Y"):
    #         print('pushing update')
    #         f = open(current_date + '.json','r') #1203075,867412
    #         string = f.read()
    #         data = json.loads( string )
    #         mongo_db.pullFromTest.insert_many( data )
    #     print('skipping update')
    #1139947
    # f = open("2021-09-01" + '.json','r')
    # string = f.read()
    # data = json.loads( string )
    # mongoHandle = MongoDatabase()
    # mongoHandle.update(data)
    
    print('done')