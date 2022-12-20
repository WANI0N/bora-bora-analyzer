from operator import mod
from traceback import print_tb
import pymongo, math, threading, json
import certifi
from datetime import datetime, timedelta
ca = certifi.where()
from dotenv import load_dotenv
load_dotenv()

import copy

class MongoDatabase:
    def __init__(self,db):
        # #connect to db
        # DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
        #       f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
        #       'retryWrites=true&w=majority'
        # client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
        # #declare self
        # self.db = client.db
        self.db = db
        #call all product ids from db
        self.dbIds = list()
        self.dbIds = self.db.products.find({},{"id":1}).distinct('id')
        # print( self.dbIds )

    def update(self,uploadDB,threads_set = False):
        #check for submit data validity
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
        
        #create hashmaps (used for integrity check during and post upload)
        self.hashMap = dict()
        i = 0
        for item in uploadDB:
            self.hashMap[ item['id'] ] = i
            i += 1
        self.uploadedItemsHashMap = {}

        #execute upload
        if threads_set:
            threadCount = 20
            threadPayload = math.floor(len(uploadDB)/threadCount)
            padding = len(uploadDB) % threadPayload
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
        else:
            printedPerCent = 0
            uploadCount = 0
            for item in uploadDB:
                self.executeUploadThread( [item] )
                uploadCount += 1
                perCent = math.floor( uploadCount/len(uploadDB)*100 )
                if printedPerCent < perCent:
                    printedPerCent = perCent
                    print(f"{printedPerCent}%")
        
        ##patching
        #obtain missing Ids
        missingIds = list()
        #retreive items where first date is not current upload date
        for item in self.db.products.find({ "history.0.date": { "$ne": uploadDB[0]['history'][0]['date'] } },{'id':1}):
            #check if item is in upload payload; if so push to list
            if item['id'] in self.hashMap:
                missingIds.append(item['id'])
        #post patching - uploading missing items to db
        for _id in missingIds:
            print("post patching..." + str(_id))
            self.db.products.update_one({'id':_id},{"$push":{"history":{
                "$each":[      uploadDB[   self.hashMap[ _id ]   ]['history'][0]     ],
                "$position":0
            }},"$set": { "image": uploadDB[   self.hashMap[ _id ]   ]['image'] }})

        print('done')

    def executeUploadThread(self,workLoad):
        for item in workLoad:
            #check for duplicate upload of an item
            if item['id'] in self.uploadedItemsHashMap:
                print(f"Duplicate upload attempt detected! -> {item['id']}")
                continue
            self.uploadedItemsHashMap[ item['id'] ] = True
            #if item on db, insert first day and update image
            if item['id'] in self.dbIds:
                self.db.products.update_one({'id':item['id']},{"$push":{"history":{
                    "$each":[      item['history'][0]      ],
                    "$position":0
                }},"$set": { "image": item['image'] }})
            else: #create new item
                self.db.products.insert_one( item )
    
    def checkForDuplicatesAndFix(self):
        #no threading
        #loop over each product
        productDuplicatesHashMap = {}
        productDuplicatesErrorLog = []
        for product in self.db.products.find({},{"id":1,"history":1}):
            if product['id'] in productDuplicatesHashMap:
                productDuplicatesErrorLog.append(f"DB Duplicate Found: {product['id']}")
            productDuplicatesHashMap[ product['id'] ] = True
            #check for duplicates, if none continue
            listOfDates = []
            for o in product['history']:
                listOfDates.append( o['date'] )
            if len(listOfDates) == len(set(listOfDates)):
                continue
            #get duplicateIndex
            hashMap = {}
            i = 0
            for dayItem in product['history']:
                if dayItem['date'] in hashMap:
                    duplicateIndex = i
                    break
                hashMap[ dayItem['date'] ] = True
                i += 1
            #remove duplicateIndex from product['history']
            del product['history'][duplicateIndex]
            #overwrite product['history']
            self.db.products.update_one({"id":product['id']},{"$set":{"history":product['history']}})
            print(f"Correcting duplicate error -> {product['id']} / index -> {duplicateIndex}")
            productDuplicatesErrorLog.append(f"Correcting duplicate error -> {product['id']} / index -> {duplicateIndex}")
        if productDuplicatesErrorLog:
            print( "\n".join(productDuplicatesErrorLog) )
        else:
            print("No product duplicates found.")
        
    def trim_to_limit(self, limit=365):
        limit_breach_date_string = (datetime.now()-timedelta(days = limit + 1)).strftime("%Y-%m-%d")
        ck = self.db.products.find_one(
            {"history": {"$elemMatch": {"date": limit_breach_date_string}}}, {"id": 1})
        if not ck:
            print(f"no breach within limit of {limit} days was found")
            return
        self.drop_date_fm_db_threaded_caller(limit_breach_date_string)
    
    def drop_date_fm_db_threaded_caller(self, target_datestring):
        target_products = list()
        i = -1
        for product in self.db.products.find(
                {"history": {"$elemMatch": {"date": target_datestring}}},
                {"id": 1, "history.date": 1}):
            i += 1
            if i % 100 == 0:
                print(f"drop_date_fm_db_threaded_caller - init - i: {i}/{len(self.dbIds)}")
            if len(product['history']) == 1:
                self.db.products.delete_one({"id": product['id']})
                continue
            for i, _ in enumerate(product['history']):
                reversed_i = len(product['history'])-1-i
                current_date = product['history'][reversed_i]['date']
                if current_date == target_datestring:        
                    target_products.append({
                            "id": product['id'],
                            "index": reversed_i,
                        })
                    break

        if len(target_products) == 0:
            print(f"No products with date: {target_datestring} were found.")
            return
        thread_count = 20
        thread_payload = math.floor(len(target_products)/thread_count)
        padding = len(target_products) % thread_payload
        threads = []
        for i in range(thread_count):
            start_index = i*thread_payload
            end_index = start_index+thread_payload
            if (i == thread_count-1):
                end_index += padding
            t = threading.Thread(target=self.drop_date_fm_db_threaded_thread, args=[i, target_products[start_index:end_index]])
            t.start()
            print(f"thread started-> {str(start_index)}-{str(end_index)}=>{end_index-start_index}")
            threads.append(t)
        for thread in threads:
            thread.join()
        print(f"{len(target_products)} were deleted/altered.")

    def drop_date_fm_db_threaded_thread(self, thread_index, products):
        for product in products:
            tmp_product = self.db.products.find_one(
                {"id": product['id']}, {"history": 1})
            hist = tmp_product['history']
            del hist[product['index']]
            self.db.products.update_one(
                {"id": product['id']}, {"$set": {"history": hist}})
            
            # if len(product['history']) == 1:
            #     # print(f"deleting item: {product['id']}...")
            #     self.db.products.delete_one({"id": product['id']})
            #     rem_count += 1
            #     continue
            # for flip_i, o in enumerate(reversed(product['history'])):
            #     i = len(product['history'])-flip_i-1
            #     if o["date"] == target_datestring:
            #         del product['history'][i]
            #         break
            # # print(f"updating item: {product['id']}...")
            # self.db.products.update_one(
            #     {"id": product['id']}, {"$set": {"history": product['history']}})
            # altered_count += 1
        print(f"Thread #{thread_index} finished - altered: {len(products)}")
    
    def clean_user_alerts(self):
        # drop from user alerts
        for user in self.db.user.find(
            {"validation_status": True},
            {"alerts": 1, "id_cookie": 1}):
            if 'alerts' not in user:
                continue
            updatedAlerts = []
            modify = False
            for alert in user["alerts"]:
                ck = self.db.products.find_one({"id": alert["productID"]}, {"id": 1})
                if not ck:
                    modify = True
                    continue
                updatedAlerts.append(alert)
            if modify:
                self.db.user.update_one(
                    {"id_cookie": user["id_cookie"]}, {"$set": {"alerts": updatedAlerts}})
        

                
