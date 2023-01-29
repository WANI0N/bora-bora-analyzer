from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import threading
import json
import time
import os
import pymongo
from datetime import datetime #, timedelta
#from bson.json_util import dumps, loads
import os.path
# import math

from mongodb import MongoDatabase
# from TEST_mongodb import MongoDatabase

import certifi
ca = certifi.where()
from dotenv import load_dotenv
load_dotenv()

class BarboraCrawler:
    def __init__(self):
        # self.baseUrl = 'https://pagrindinis.barbora.lt'
        self.baseUrl = 'https://barbora.lt'
        self.topLinks = list()
        self.productPages = dict()
        self.needleKeys = [
            'id','title','category_name_full_path','brand_name','image','comparative_unit','history'
        ]
        self.historyObjKeys = [
            'price','comparative_unit_price','date','active'
        ]
        self.database = []
    
    def urlToSoup(self,url = None):
        targetUrl = self.baseUrl
        if not url: ## change: root url on it's own now shows select county page (same redirect for https://pagrindinis.barbora.lt, if route added: works)
            targetUrl = 'https://barbora.lt/darzoves-ir-vaisiai'
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
        if not self.topLinks:
            print('Failed to export Top Links')
            return
        for baseLink in self.topLinks:
            self.productPages[baseLink] = False
        
        threads = list()
        threadCount = 12
        self.threadWaitList = list()
        for i in range(threadCount):
            self.threadWaitList.append(True)
            t = threading.Thread(target=self.threadLooper, args=[ i ])
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()

        ## removing keys out of target needle, trim id, add date
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        for i, item in enumerate(self.database):
            self.database[i]["history"] = [{
                # 'price':item['price'],
                'price':round(item['price'], 2),
                # 'comparative_unit_price':item['comparative_unit_price'],
                'comparative_unit_price':round(item['comparative_unit_price'], 2),
                'date':current_date,
                'active':item['active'],
            }]
            self.database[i] = { key: item[key] for key in self.needleKeys }
            self.database[i]["id"] = self.database[i]["id"].lstrip("0")
        
    def threadLooper(self,index):
        exist = True
        mark = 0
        while exist:
            if self.getGreenLight(index):
                link = self.getNewThreadLink()
                if link:
                    self.productPages[link] = True
                    self.threadWaitList[index] = False
                    self.getProductsFromPage(link)
                elif mark < 8:
                    time.sleep(0.5)
                    mark += 1
                else:
                    exist = False
        print(f'thread number {index} finished.')

    def getGreenLight(self,index):
        i = 0
        for state in self.threadWaitList:
            if (i < index):
                if state:
                    print(f"Thread {index} is waiting for thread {i}")
                    return False
            else:
                break
            i += 1
        return True
        

    def getProductsFromPage(self,childLink):
        print('extracting... ' + childLink)
        soup = self.urlToSoup(childLink)
        for div in soup.select('div[class*="b-product--wrap clearfix b-product--js-hook"]'):
            string = div.get('data-b-for-cart')
            string = string.replace('&quot;',"\"")
            obj = json.loads(string)
            if 'b-product-outofstock' in div['class']:
                obj['active'] = False
            else:
                obj['active'] = True
            self.database.append(obj)
        pageLinks = []
        for container in soup.find_all('ul', "pagination"):
            for link in container.find_all('a'):
                pageLinks.append( link.get('href') )

        self.appendNewPageLinks(pageLinks)
    
    def appendNewPageLinks(self,pageLinks):
        for pageLink in pageLinks:
            if pageLink not in self.productPages:
                self.productPages[pageLink] = False
    
    def getNewThreadLink(self):
        # for pageLink,status in self.productPages.items():
        for pageLink,status in sorted(list(self.productPages.items()), reverse=True):
            if not status:
                return pageLink
        return False

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


#updating db if current date not present, manual for now
if __name__ == "__main__":
    crawler = BarboraCrawler()
    crawler.analyze()
    crawler.outputDatabase()
