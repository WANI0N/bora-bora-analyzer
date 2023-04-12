from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import threading
import json
import time
import os
from datetime import datetime
import os.path


import certifi
ca = certifi.where()
from dotenv import load_dotenv
load_dotenv()

class BarboraCrawler:
    def __init__(self):
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
    
    def get_url_data(self, url = None, soap: bool = True):
        targetUrl = self.baseUrl
        if not url: 
            targetUrl = 'https://barbora.lt/darzoves-ir-vaisiai'
        if url:
            targetUrl = targetUrl + url
        try:
            page = urlopen(targetUrl)
        except HTTPError as err:
            raise err
        except URLError as err:
            raise err
        except:
            raise "Unknown error"
        if soap:
            return BeautifulSoup(page, 'html.parser')
        else:
            return page.read().decode("utf-8")
    
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
                'price':round(item['price'], 2),
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
        soup = self.get_url_data(f"/{childLink}")
        for div in soup.select('div[class*="b-product--wrap clearfix b-product--js-hook"]'):
            string = div.get('data-b-for-cart')
            string = string.replace('&quot;',"\"")
            obj = json.loads(string)
            if 'b-product-outofstock' in div['class']:
                obj['active'] = False
            else:
                obj['active'] = True
            if round(obj['price'], 2) == 0:
                continue
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
        for pageLink, status in sorted(list(self.productPages.items()), reverse=True):
            if not status:
                return pageLink
        return False

    def getTopLinks(self):
        # extracts top category product links from main page
        raw_html = self.get_url_data(None, False)
        arr = raw_html.split("window.b_categories = ")
        c_arr = arr[1].split(";")
        try:
            page_data = json.loads(c_arr[0])
        except json.JSONDecodeError as err:
            raise err
        except TypeError as err:
            raise err
        if 'categories' not in page_data:
            print("key 'categories' not present in json data")
            return
        for o in page_data['categories']:
            self.topLinks.append( o['url'] )


    def outputDatabase(self, format='json'):
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d") # - %H-%M-%S")
        if os.path.isfile(current_date + ".json"):
            os.remove(current_date + ".json")
        f = open(current_date + ".json","a")
        f.write( json.dumps(self.database,indent='\t') )
        f.close()


if __name__ == "__main__":
    crawler = BarboraCrawler()
    crawler.analyze()
    crawler.outputDatabase()
