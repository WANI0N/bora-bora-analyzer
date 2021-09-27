
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
            }}})
        # print(missingIds)
        print('done')

    def executeUploadThread(self,workLoad):
        for item in workLoad:
            if item['id'] in self.dbIds:
                self.db.products.update_one({'id':item['id']},{"$push":{"history":{
                    "$each":[      item['history'][0]      ],
                    "$position":0
                }}})
            else:
                self.db.products.insert_one( item )

# test_Obj = {
#     "variation":{
#         "tops":[
#             {
#                 "id":'131231',
#                 "value":2
#             },
#             {
#                 "id":'131231',
#                 "value":34
#             },
#             {
#                 "id":'131231',
#                 "value":12
#             },
#             {
#                 "id":'131231',
#                 "value":3
#             },
#             {
#                 "id":'131231',
#                 "value":43
#             }
#         ],
#         "lows":[]
#     },
#     "availability":{
#         "tops":[],
#         "lows":[
#             {
#                 "id":'131231',
#                 "value":2
#             },
#             {
#                 "id":'131231',
#                 "value":34
#             },
#             {
#                 "id":'131231',
#                 "value":12
#             },
#             {
#                 "id":'131231',
#                 "value":3
#             },
#             {
#                 "id":'131231',
#                 "value":43
#             }
#         ]
#     },
#     "allTimePrice":{
#         "tops":[
#             {
#                 "id":'131231',
#                 "value":2
#             },
#             {
#                 "id":'131231',
#                 "value":34
#             },
#             {
#                 "id":'131231',
#                 "value":12
#             },
#             {
#                 "id":'131231',
#                 "value":3
#             },
#             {
#                 "id":'131231',
#                 "value":43
#             }
#         ],
#         "lows":[]
#     }
# }



# print( recurrsion_sort(test_Obj ) )


    # def getProducts(self):
    #     try:
    #         for title in mongo_db.products.find({},{"title":1}).distinct('title'):
    #             self.productTitles.append(title)
    #     except (AutoReconnect, ConnectionFailure) as e:
    #         print(e)
    #         return
    # def analyze(self):
        
    #     i = 0
    #     for title in self.productTitles:
    #         if (i == 100):
    #             break
    #         product = mongo_db.products.find({"title":title},{"price":1,"date":1}) #,"comparative_unit":1,"comparative_unit_price":1,"date":1})
            
    #         product = list(product)
    #         # if (i == 0):
    #         #     product = [
    #         #         {"price":1},
    #         #         {"price":2},
    #         #         {"price":3},
    #         #         {"price":2},
    #         #         {"price":1},
    #         #         {"price":3},
    #         #         {"price":4},
    #         #         {"price":1},
    #         #         {"price":2},
    #         #         {"price":3},
    #         #     ]
    #         # if (i == 1):
    #         #     product = [
    #         #         {"price":10},
    #         #         {"price":20},
    #         #         {"price":30},
    #         #         {"price":40},
    #         #         {"price":50},
    #         #         {"price":60},
    #         #         {"price":70},
    #         #         {"price":80},
    #         #         {"price":90},
    #         #         {"price":100},
    #         #     ]
    #         self.recordHighlights(title,product)
    #         i += 1
    # def recordHighlights(self,title,product):
    #     #analyzing variation
    #     prices = list()
    #     for record in product:
    #         prices.append(round(record["price"],2))
    #         # print(record)
    #         # print(record["price"])
    #     #print(prices)
        
        
    #     mean = round(sum(prices)/len(prices),2)
    #     deviation_sqr = [ (price - mean) ** 2 for price in prices ]
    #     #print(deviation_sqr)
    #     variance = sum(deviation_sqr)/len(prices)
    #     #print(variance)
    #     stdDev = math.sqrt(variance)
    #     #print(mean)
    #     #print(stdDev)
    #     #_min = min(mean,stdDev)
    #     diff = abs(mean-stdDev)
    #     # print(mean)
    #     perc = diff/mean*100
    #     perc_diff = 100-perc
    #     print(perc_diff)
    #     if (abs(perc_diff) > 10):
    #         print(title)
    #         print(perc)
    #         print(prices)

    # def analyzeProductVariation(self,prices):
        
    #     mean = sum(prices)/len(prices)
    #     deviation = [ price - mean for price in prices ]
    #     print(deviation)
    #     _min = min(prices)
    #     _max = max(prices)
    #     diff = abs(_min-_max)
    #     perc = diff/_min*100
    #     print(title)
    #     print(perc)
# keepKeys = ['id','history']
    # existingKeys = [k for k in data[0] ]
    # i = 0
    # smallData = []
    # for i in range(len(data)):
    #     # for k in existingKeys:
    #     #     if k not in keepKeys:
    #     #         data[i].pop(k)
    #     smallData.append(data[i])
    #     if (i == 2):
    #         break
    
    
    # mongo_db.pushToTest.insert_many( data )


# ## updating existing db
    # f = open('2021-08-24.json','r')
    # string = f.read()
    # data = json.loads( string )

    # ## db patching
    # notUpdatedProducts = list()
    # for notUpdatedProduct in mongo_db.products.find({"history": { "$size": 1 , "$elemMatch": {"date": "2021-08-23"} }}):
    #     notUpdatedProducts.append( notUpdatedProduct )
    #         # print(product)
    # # print( len(notUpdatedProducts) )
    # list_cur = list(notUpdatedProducts)
    # json_string = dumps(list_cur, indent = 2)
    # potentialErrorsData = json.loads(json_string)
    
    # hashMap = dict()
    # i = 0
    # for product in data:
    #     hashMap[ product["id"] ] = i
    #     i += 1

    # correctedCount = 0
    # checkedCount = len(notUpdatedProducts)
    # for product in potentialErrorsData:
    #     if product['id'] in hashMap:
    #         mongo_db.products.update_one({'id':product['id']},{"$push":{"history":{
    #             "$each":[      data[   hashMap[ product['id'] ]   ]['history'][0]      ],
    #             "$position":0
    #         }}})
    #         correctedCount += 1
    # print(correctedCount)
    # existingIdsUpdate = 0
    # novelIdsUpdate = 0
    # duplicateProductsError = False
    # duplicateProductsList = list()
    # for product in data:
    # # for product in crawler.database:
    #     idPresent = False
    #     targetID = product['id']
    #     i = 0
    #     for _id in mongo_db.products.find({'id':targetID}):
    #         if (i == 1):
    #             duplicateProductsError = True
    #             duplicateProductsList.append()
    #         idPresent = True
    #         i += 1
    #     if idPresent:
    #         mongo_db.products.update_one({'id':targetID},{"$push":{"history":{
    #             "$each":[ product['history'][0] ],
    #             "$position":0
    #         }}})
    #         existingIdsUpdate += 1
    #     else:
    #         mongo_db.products.insert_one(product)
    #         novelIdsUpdate += 1
    # print("existingIdsUpdate",existingIdsUpdate)
    # print("novelIdsUpdate",novelIdsUpdate)
    # if duplicateProductsError:
    #     print( 'duplicateProductsError' )
    #     print( duplicateProductsList )
    ## pushing innitial db
    # from bson.son import SON
    # mongo_db.products.drop()
    # f = open('2021-08-23.json','r')
    # string = f.read()
    # data = json.loads( string )
    # newData = list()
    # for item in data:
    #     item["history"] = SON([ ("comparative_unit_price", item["history"]["comparative_unit_price"]) , ("date", item["history"]["date"]) , ("price", item["history"]["price"]) ])
    #     newData.append(item)
    # print(data)
    # mongo_db.products.insert_many(data)

    ## query ids
    ## pulls most recent history object
    # ids = list()
    # #for _id in mongo_db.products2.find({"history": {"$elemMatch": {"date": "2021-08-19"}}},{"id":1,"history": {"$slice": 1 }}):
    # for _id in mongo_db.products2.find({},{"history": {"$slice": 1 }}):
    #     ids.append(_id)
    # list_cur = list(ids)
    # json_string = dumps(list_cur, indent = 2)
    # json_data = json.loads(json_string)
    # print(json_string)
    
    ## updating db, place the history object to start of the array
    # targetID = '1115160'
    # print('BEFORE')
    # for _id in mongo_db.products2.find({'id':targetID}):
    #     print(_id)
    # mongo_db.products2.update_one({'id':targetID},{"$push":{"history":{
    #     "$each":[{"date": "2021-08-22","price":3.89,"comparative_unit_price": 4.12}],
    #     "$position":0
    # }}})
    # print('AFTER')
    # for _id in mongo_db.products2.find({'id':targetID}):
    #     print(_id)



# crawler = BarboraCrawler()
# startTime = time.perf_counter()
# crawler.analyze()
# crawler.outputDatabase()
# # # print(
# # #     crawler.childLinks
# # # )
# print(
#     time.perf_counter()-startTime
# )




### updating existing db
    ## if from file
    # now = datetime.now()
    # current_date = now.strftime("%Y-%m-%d")
    # f = open(current_date + '.json','r')
    # string = f.read()
    # data = json.loads( string )
    # ## creating hash map, adding index
    # hashMap = dict()
    # i = 0
    # for item in data:
    #     hashMap[ item['id'] ] = i
    #     i += 1
    # localDbItems = str(i)
    # ## retreiving ids from mongo
    # dbIds = list()
    # for _id in mongo_db.products.find({},{"id":1}).distinct('id'):
    #     dbIds.append(_id)
    # ## looping over ids
    # existingIdsUpdate = 0
    # novelIdsUpdate = 0
    # i = 0
    # for _id, dataIndex in hashMap.items():
    #     if _id in dbIds:
    #         existingIdsUpdate += 1
    #         print(str(dataIndex) + "/" + localDbItems,"updating..." + str(_id))
    #         mongo_db.products.update_one({'id':_id},{"$push":{"history":{
    #             "$each":[      data[   dataIndex   ]['history'][0]      ],
    #             "$position":0
    #         }}})
    #     else:
    #         novelIdsUpdate += 1
    #         print(str(dataIndex) + "/" + localDbItems,"inserting..." + str(_id))
    #         mongo_db.products.insert_one( data[ dataIndex ])
    #     i += 1
    # print( "existingIdsUpdate",existingIdsUpdate )
    # print( "novelIdsUpdate",novelIdsUpdate )










    


    ## inserting new db
    
    # now = datetime.now()
    # current_date = now.strftime("%Y-%m-%d")
    # f = open(current_date + '.json','r')
    # string = f.read()
    # data = json.loads( string )
    

    # dbIds = list()
    # for _id in mongo_db.products.find({},{"id":1}).distinct('id'):
    #     dbIds.append(_id)
    
    # threadCount = 20
    # threadPayload = math.floor(len(data)/threadCount)
    # padding = len(data) % threadPayload
    # print(len(data))
    # print( len(data)/threadCount )
    # print(threadPayload)
    # print(padding)
    
    # threads = []
    # for i in range(threadCount):
    #     startIndex = i*threadPayload
    #     endIndex = startIndex+threadPayload-1
    #     if (i == threadCount-1):
    #         endIndex += padding
    #     t = threading.Thread(target=executeUploadThread, args=[ dbIds,data[startIndex:endIndex] ])
    #     t.start()
    #     print("thread started-> " + str(startIndex) + "-" + str(endIndex))
    #     threads.append(t)

    # i = 0
    # for thread in threads:
    #     print("thread #" + str(i) + " finished")
    #     thread.join()
    #     i += 1

    ##patching
    # hashMap = dict()
    # i = 0
    # for item in data:
    #     hashMap[ item['id'] ] = i
    #     i += 1
    # missingIds = list()
    # asd = []
    # for item in mongo_db.products.find({ "history.0.date": { "$ne": "2021-08-27" } },{'id':1}):
    #     if item['id'] in hashMap:
    #         missingIds.append(item['id'])
    # # for _id in missingIds:
    # #     print("updating..." + str(_id))
    # #     mongo_db.products.update_one({'id':_id},{"$push":{"history":{
    # #         "$each":[      data[   hashMap[ _id ]   ]['history'][0]     ],
    # #         "$position":0
    # #     }}})
    # print(asd)
    # print(missingIds)