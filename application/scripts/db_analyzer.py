import threading
import json
import time
import os
import pymongo
# from pymongo.errors import AutoReconnect, ConnectionFailure
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bson.json_util import dumps, loads
import math
#from application.routes import parseMongo
#from application import routes.parseMongo

from product_analyzer import ProductAnalyzer


load_dotenv()


def recurrsion_sort(data,_id,pushData, submitKey = None):
    ignoreItems = ["unique_price_count"]
    for k, content in data.items():
        if isinstance(content,dict):
            data[k] = recurrsion_sort(content,_id,pushData,k)
        elif isinstance(content,list):
            pushObj = {"id":_id}
            if submitKey in ignoreItems:
                continue
            if (submitKey != "topToday"):
                if (submitKey == "var_perc"):
                    pushObj["stdDev"] = round(pushData["var_stdDev"],2)
                pushObj["value"] = round(pushData[submitKey],2)
                if (len(content) < 20):
                    content.append( pushObj )
                elif (k == "tops"):
                    if (content[ 0 ]["value"] < pushObj['value']):
                        content[ 0 ] = pushObj
                elif (k == "lows"):
                    if (submitKey == "availability_perc"):
                        if (pushObj['value'] == 0):
                            continue
                    if (content[ 19 ]["value"] > pushObj['value']):
                        content[ 19 ] = pushObj
                if content:
                    data[k] = sorted(content, key=lambda k: k['value'])
            else:
                pushObj["value"] = pushData['max'] if (k == "tops") else pushData['min']
                if not pushObj['value']:
                    continue
                pushObj["sortingValue"] = pushData["unique_price_count"]
                if (len(content) < 20):
                    content.append( pushObj )
                elif (content[ 0 ]["sortingValue"] < pushObj['sortingValue']):
                    content[ 0 ] = pushObj
                if content:
                    data[k] = sorted(content, key=lambda k: k['sortingValue'])
    return data

def translateCats(targetArr,sourceData):
    if not sourceData:
        return targetArr
    returnArr = list()
    for w in targetArr:
        # appendWord = sourceData[w] if w in sourceData else w
        # returnArr.append( appendWord )
        returnArr.append( sourceData[w] if w in sourceData else w )
        
    return returnArr

class DbAnalyzer:
    def __init__(self,db,updateCategories = False):
        self.db = db
        self.dbIds = self.db.products.find({},{"id":1}).distinct('id')
        self.updateCategories = updateCategories
        self.highlights = {
            "var_stdDev":{
                "tops":[],
                "lows":[]
            },
            "var_perc":{
                "tops":[],
                "lows":[]
            },
            "topToday":{
                "tops":[],
                "lows":[]
            },
            "availability_perc":{
                "tops":[],
                "lows":[]
            },
        }
        # self.dayCount = dayCount
        # self.dateCutOff = datetime.now()-timedelta(days=dayCount)
        # self.totalMeansData = dict()
        self.dbStatsData = dict()
        for i in range(50):
            today = datetime.now()-timedelta(days=i)
            today = today.strftime("%Y-%m-%d")
            if self.db.products.find_one({'history.0.date':today},{'id':1}):
                self.dbUpdateDate = today
                break
        
        # self.TEST_DuplicateList = []

    def analyze(self):
        batchSize = 200
        dbSubmitCount = math.floor(len(self.dbIds)/batchSize)
        dbSubmitPadding = len(self.dbIds) % batchSize
        
        threads = []
        i = 0
        for i in range(dbSubmitCount):
            # if (i == 1):
            #     break
            startIndex = i*batchSize
            endIndex = startIndex+batchSize
            if (i == dbSubmitCount-1):
                endIndex += dbSubmitPadding
            products = self.db.products.find({"id": {"$in": self.dbIds[startIndex:endIndex]}},{"history":1,"id":1},batch_size=batchSize)
            products = list(products)
            t = threading.Thread(target=self.threadSubmit, args=[products])
            # t = threading.Thread(target=self.threadSubmitTEST, args=[products])
            t.start()
            print("thread started-> " + str(startIndex) + "-" + str(endIndex))
            threads.append(t)
            i += 1
        i = 0
        for thread in threads:
            print("thread #" + str(i) + " finished")
            thread.join()
            i += 1
        
        self.highlights["var_stdDev"]["tops"] = self.highlights["var_stdDev"]["tops"][::-1]
        self.highlights["var_perc"]["tops"] = self.highlights["var_perc"]["tops"][::-1]
        self.highlights["availability_perc"]["tops"] = self.highlights["availability_perc"]["tops"][::-1]
        self.highlights["topToday"]["tops"] = self.highlights["topToday"]["tops"][::-1]
        self.highlights["topToday"]["lows"] = self.highlights["topToday"]["lows"][::-1]

    # def threadSubmitTEST(self,products):
    #     for product in products:
    #         listOfElems = []
    #         for o in product['history']:
    #             listOfElems.append( o['date'] )
    #         if len(listOfElems) == len(set(listOfElems)):
    #             continue
    #         self.TEST_DuplicateList.append({
    #             "id:":product['id'],
    #             "data":product['history']
    #         })

    def threadSubmit(self,products):
        for product in products:
            prodAnalyzer = ProductAnalyzer(product['history'],self.dbUpdateDate)
            results = prodAnalyzer.getResultsAsDict()
            self.highlights = recurrsion_sort(self.highlights,product['id'],results)
            
            productDbStats = prodAnalyzer.getDifferenceToMeanList()
            for item in productDbStats:
                if item['date'] not in self.dbStatsData:
                    self.dbStatsData[ item['date'] ] = list()
                self.dbStatsData[ item['date'] ].append( item['perc_diff'] )
    
    def getDbStatsDataFinal(self):
        
        self.dbStatsDataFinal = []
        for date,list in self.dbStatsData.items():
            diff_perc = sum(list)/len(list)
            self.dbStatsDataFinal.append(dict({
                "date":date,
                "diff_perc":diff_perc,
                "count":len(list),
                "total":len(self.dbIds),
                "perCent":len(list)/len(self.dbIds)*100
            }))
        self.dbStatsData = {}
    
    def executeAndDiscard(self):
        self.analyze()
        # self.getTotalMeans()
        self.getDbStatsDataFinal()
        
        # self.totalMeansData = [] #memory extensive

        if (os.path.exists('temp/highlights.json')):
            os.remove('temp/highlights.json')
        f = open('temp/highlights.json','a')
        f.write( json.dumps(self.highlights,indent="\t") )
        f.close()
        
        if (os.path.exists('temp/dbStatsDataFinal.json')):
            os.remove('temp/dbStatsDataFinal.json')
        f = open('temp/dbStatsDataFinal.json','a')
        f.write( json.dumps(self.dbStatsDataFinal,indent="\t") )
        f.close()
        # if (os.path.exists('temp/totalMeansFinal.json')):
        #     os.remove('temp/totalMeansFinal.json')
        # f = open('temp/totalMeansFinal.json','a')
        # f.write( json.dumps(self.totalMeansFinal,indent="\t") )
        # f.close()
        if self.updateCategories:
            self.getCategories()
            if (os.path.exists('temp/categoryPathing.json')):
                os.remove('temp/categoryPathing.json')
            f = open('temp/categoryPathing.json','a')
            f.write( json.dumps(self.categoryPathing,indent="\t") )
            f.close()

            if (os.path.exists('temp/categoryCounts.json')):
                os.remove('temp/categoryCounts.json')
            f = open('temp/categoryCounts.json','a')
            f.write( json.dumps(self.categoryCounts,indent="\t") )
            f.close()

    def getCategories(self):
        categoryList = list()
        categoryList = self.db.products.find({},{"category_name_full_path":1}).distinct('category_name_full_path')
        
        catsTranslation = {}
        if (os.path.exists('temp/catsTranslation.json')):
            f=open('temp/catsTranslation.json','r',encoding='utf-8')
            catsTranslation = json.loads( f.read() )
            f.close()
        
        self.categoryPathing = dict()
        self.categoryCounts = dict()

        for path in categoryList:
            arr = path.split('/')
            if arr[0]:
                if arr[0] not in self.categoryPathing:
                    self.categoryPathing[ arr[0] ] = dict()
            if (len(arr) == 1): # for path repeating in name, e.g. cat a/milks/milks
                continue
            if arr[1]:
                if arr[1] not in self.categoryPathing[ arr[0] ]:
                    self.categoryPathing[ arr[0] ][ arr[1] ] = list()
            if (len(arr) == 2): # for path repeating in name, e.g. cat a/milks/milks
                continue
            if arr[2]:
                if arr[2] not in self.categoryPathing[ arr[0] ][ arr[1] ]:
                    self.categoryPathing[ arr[0] ][ arr[1] ].append( arr[2] )
                    submitPath = arr[0] + "/" + arr[1] + "/" + arr[2]
                    translatedCatArr = translateCats(arr,catsTranslation)
                    self.categoryCounts[ translatedCatArr[2] ] = dict({
                        "top":translatedCatArr[0],
                        "mid":translatedCatArr[1],
                        "count":submitPath
                        # "count":self.db.products.count_documents({"category_name_full_path":submitPath})
                    })
        
        threads = []
        for k in self.categoryCounts:
            t = threading.Thread(target=self.catThreadSubmit, args=[k])
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()
        

    def catThreadSubmit(self,key):
        self.categoryCounts[key]["count"] = self.db.products.count_documents({"category_name_full_path":self.categoryCounts[key]["count"]})
        
    

if __name__ == "__main__":
    # def parseMongo(data,method='api'):
    #     list_cur = list(data)
    #     json_data = dumps(list_cur, indent = 2)
    #     if (method == 'api'):
    #         return json.loads(json_data)
    #     else:
    #         return json_data
    
    import certifi
    ca = certifi.where()
    DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
              f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
              'retryWrites=true&w=majority'
    client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    mongo_db=client.db

    analyzer = DbAnalyzer(mongo_db)
    # analyzer.getCategories()
    analyzer.executeAndDiscard()
    
    
    print('done')
    

    # analyzer = DbAnalyzer("",[])
    # f = open('gigant.json','r') #1203075,867412
    # string = f.read()
    # data = json.loads(string)
    # analyzer.totalMeans = data
    
    
    # if (os.path.exists('gigant.json')):
    #     os.remove('gigant.json')
    # f=open('gigant.json','a')
    # f.write(json.dumps( analyzer.totalMeans,indent='\t' ))
    # f.close()
    # if (os.path.exists('temp/highlights.json')):
    #     os.remove('temp/highlights.json')
    # f = open('temp/highlights.json','a')
    # f.write( json.dumps(analyzer.highlights,indent="\t") )
    # f.close()
    # print(
    #     # json.dumps(analyzer.highlights["topToday"],indent="\t")
    #     json.dumps(analyzer.highlights,indent="\t")
    # )
    