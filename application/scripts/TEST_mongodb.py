import pymongo, math, threading, os

import certifi
ca = certifi.where()

from dotenv import load_dotenv
load_dotenv()

class MongoDatabase:
    def __init__(self):
        DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
              f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
              'retryWrites=true&w=majority'
        client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
        self.db = client.db
        self.dbIds = list()
        
        self.dbIds = self.db.productsTEST.find({},{"id":1}).distinct('id')
        

    def update(self,uploadDB,threads_set = False):
        if not isinstance(uploadDB,list):
            print('invalid uploadDB')
            return
        if 'date' not in uploadDB[0]['history'][0]:
            print('invalid uploadDB; missing history')
            return
        
        ck = self.db.productsTEST.find_one({'history.0.date':uploadDB[0]['history'][0]['date']},{'id':1})
        if ck:
            print(f"Server database already contains data of {uploadDB[0]['history'][0]['date']}")
            return
        
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
                print(printedPerCent)

        ##patching
        hashMap = dict()
        i = 0
        for item in uploadDB:
            hashMap[ item['id'] ] = i
            i += 1
        missingIds = list()
        
        # now = datetime.now()
        # current_date = now.strftime("%Y-%m-%d")
        for item in self.db.productsTEST.find({ "history.0.date": { "$ne": uploadDB[0]['history'][0]['date'] } },{'id':1}):
            if item['id'] in hashMap:
                missingIds.append(item['id'])
        for _id in missingIds:
            print("post patching..." + str(_id))
            self.db.productsTEST.update_one({'id':_id},{"$push":{"history":{
                "$each":[      uploadDB[   hashMap[ _id ]   ]['history'][0]     ],
                "$position":0
            }},"$set": { "image": uploadDB[   hashMap[ _id ]   ]['image'] }})
            
        # print(missingIds)
        print('done')

    def executeUploadThread(self,workLoad):
        for item in workLoad:
            if item['id'] in self.dbIds:
                self.db.productsTEST.update_one({'id':item['id']},{"$push":{"history":{
                    "$each":[      item['history'][0]      ],
                    "$position":0
                }},"$set": { "image": item['image'] }})
            else:
                self.db.productsTEST.insert_one( item )