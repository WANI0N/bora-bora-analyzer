import json
import os
import pymongo
from datetime import datetime, timedelta
from dotenv import load_dotenv
# from bson.json_util import dumps, loads
import math

from functions import convert_history_to_old_format

from product_analyzer import ProductAnalyzer


load_dotenv()


def recurrsion_sort(data,_id,pushData, submitKey = None):
    ignoreItems = ["unique_price_count","priceDropPerCent","priceDropDate","lastActiveDate"]
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
                if (submitKey == "availability_perc"):
                    pushObj["lastActiveDate"] = pushData["lastActiveDate"]
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
                pushObj["priceDropDate"] = pushData["priceDropDate"]
                pushObj["priceDropPerCent"] = round(pushData["priceDropPerCent"],2)
                if (len(content) < 20):
                    content.append( pushObj )
                elif (content[ 0 ]["sortingValue"] < pushObj['sortingValue']):
                    content[ 0 ] = pushObj
                if content:
                    data[k] = sorted(content, key=lambda k: k['sortingValue'])
    return data

def translate_cats(targetArr: list, sourceData: list) -> list:
    if not sourceData:
        return targetArr
    returnArr = list()
    for w in targetArr:
        returnArr.append( sourceData[w] if w in sourceData else w )
        
    return returnArr

class DbAnalyzer:
    def __init__(self,db):
        self.db = db
        self.dbIds = self.db.products.find({},{"id":1}).distinct('id')
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
        self.db_stats_data = dict()
        for i in range(100):
            today = datetime.now()-timedelta(days=i)
            today = today.strftime("%Y-%m-%d")
            if self.db.products.find_one({'history.0.end-date': today}, {'id': 1}):
                self.db_update_date = today
                break

    def analyze(self):
        batch_size = 500
        db_submit_count = math.floor(len(self.dbIds)/batch_size)
        db_submit_padding = len(self.dbIds) % batch_size
        for i in range(db_submit_count):
            start_index = i*batch_size
            end_index = start_index+batch_size
            if (i == db_submit_count-1):
                end_index += db_submit_padding
            
            products = self.db.products.find({"id": {"$in": self.dbIds[start_index:end_index]}},{"history": 1, "id": 1},batch_size=batch_size)
            products = list(products)
            
            self.analyze_batch(products)
            
            print(f"finished -> {str(start_index)} - {str(end_index)}")
            
        
        self.highlights["var_stdDev"]["tops"] = self.highlights["var_stdDev"]["tops"][::-1]
        self.highlights["var_perc"]["tops"] = self.highlights["var_perc"]["tops"][::-1]
        self.highlights["availability_perc"]["tops"] = self.highlights["availability_perc"]["tops"][::-1]
        self.highlights["topToday"]["tops"] = self.highlights["topToday"]["tops"][::-1]
        self.highlights["topToday"]["lows"] = self.highlights["topToday"]["lows"][::-1]

    def analyze_batch(self, products: list):
        for product in products:
            old_hist_format = convert_history_to_old_format(product['history'])
            
            prodAnalyzer = ProductAnalyzer(
                old_hist_format,
                self.db_update_date
                )
            results = prodAnalyzer.getResultsAsDict()
            self.highlights = recurrsion_sort(self.highlights,product['id'],results)
            
            productDbStats = prodAnalyzer.getDifferenceToMeanList()
            for item in productDbStats:
                if item['date'] not in self.db_stats_data:
                    self.db_stats_data[ item['date'] ] = list()
                self.db_stats_data[ item['date'] ].append( item['perc_diff'] )
    
    def get_final_db_stats(self):
        
        self.db_stats_data_final = []
        for date,list in self.db_stats_data.items():
            diff_perc = sum(list)/len(list)
            self.db_stats_data_final.append(dict({
                "date":date,
                "diff_perc":diff_perc,
                "count":len(list),
                "total":len(self.dbIds),
                "perCent":len(list)/len(self.dbIds)*100
            }))
        ##sort by date ensures graph consistency
        self.db_stats_data_final = sorted(self.db_stats_data_final, key = lambda i: i['date'],reverse=True)
        self.db_stats_data = {}
    
    def analyze_and_push(self, update_categories: bool = False, local_update: bool = False):
        print("analyzing products...")
        self.analyze()
        print("compiling final stats...")
        self.get_final_db_stats()
        print("pushing results to db...")
        if local_update:
            if (os.path.exists('temp/dbStatsDataFinal.json')):
                os.remove('temp/dbStatsDataFinal.json')
            f = open('temp/dbStatsDataFinal.json','a')
            f.write( json.dumps(self.db_stats_data_final,indent="\t") )
            f.close()

            if (os.path.exists('temp/highlights.json')):
                os.remove('temp/highlights.json')
            f = open('temp/highlights.json','a')
            f.write( json.dumps(self.highlights,indent="\t") )
            f.close()
            if update_categories:
                self.get_categories()
                if (os.path.exists('temp/categoryPathing.json')):
                    os.remove('temp/categoryPathing.json')
                f = open('temp/categoryPathing.json','a')
                f.write( json.dumps(self.category_pathing,indent="\t") )
                f.close()

                if (os.path.exists('temp/categoryCounts.json')):
                    os.remove('temp/categoryCounts.json')
                f = open('temp/categoryCounts.json','a')
                f.write( json.dumps(self.category_counts,indent="\t") )
                f.close()
        else:
            self.db.dbStatsDataFinal.drop()
            self.db.dbStatsDataFinal.insert_many(self.db_stats_data_final)
        
            self.db.highlights.drop()
            self.db.highlights.insert_one(self.highlights)
            if update_categories:
                self.get_categories()
                self.db.categoryPathing.drop()
                self.db.categoryPathing.insert_one(self.category_pathing)
        
                self.db.categoryCounts.drop()
                self.db.categoryCounts.insert_one(self.category_counts)
        

    def get_categories(self):
        category_list = list()
        category_list = self.db.products.find({},{"category_name_full_path":1}).distinct('category_name_full_path')
        
        cats_translation = {}
        if (os.path.exists('application/static/cats_translation.json')):
            f=open('application/static/cats_translation.json','r',encoding='utf-8')
            cats_translation = json.loads( f.read() )
            f.close()
        
        self.category_pathing = dict()
        self.category_counts = dict()

        for path in category_list:
            arr = path.split('/')
            if arr[0]:
                if arr[0] not in self.category_pathing:
                    self.category_pathing[ arr[0] ] = dict()
            if (len(arr) == 1): # for path repeating in name, e.g. cat a/milks/milks
                continue
            if arr[1]:
                if arr[1] not in self.category_pathing[ arr[0] ]:
                    self.category_pathing[ arr[0] ][ arr[1] ] = list()
            if (len(arr) == 2): # for path repeating in name, e.g. cat a/milks/milks
                continue
            if arr[2]:
                if arr[2] not in self.category_pathing[ arr[0] ][ arr[1] ]:
                    self.category_pathing[ arr[0] ][ arr[1] ].append( arr[2] )
                    submit_path = arr[0] + "/" + arr[1] + "/" + arr[2]
                    translated_cat_arr = translate_cats(arr, cats_translation)
                    self.category_counts[ translated_cat_arr[2] ] = dict({
                        "top":translated_cat_arr[0],
                        "mid":translated_cat_arr[1],
                        "count":self.db.products.count_documents({"category_name_full_path":submit_path})
                    })
    

if __name__ == "__main__":
    import certifi
    ca = certifi.where()
    DATABASE_URL=f'mongodb+srv://{os.environ.get("DB_NAME_2")}:{os.environ.get("DB_PASSWORD_2")}'\
        '@cluster0.ichgboc.mongodb.net/?retryWrites=true&w=majority'
    client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    mongo_db=client.db

    analyzer = DbAnalyzer(mongo_db)
    analyzer.analyze_and_push(True, True)
    print('done')

    