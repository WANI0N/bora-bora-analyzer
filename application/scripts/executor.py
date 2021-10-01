from db_analyzer import DbAnalyzer
from webcrawler import BarboraCrawler
from TEST_mongodb import MongoDatabase
# from mongodb import MongoDatabase
import pymongo, os
import json
import certifi
ca = certifi.where()
from functions import *
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    

    ##test 1 worked, day pushed to productsTEST db
    # crawler = BarboraCrawler()
    # crawler.analyze()

    # mongoHandle = MongoDatabase()
    # mongoHandle.update(crawler.database)
    
    ##test two - file creation
    f=open('temp/testFIle.txt','a')
    f.write('testString')
    f.close()
    # DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
    #           f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
    #           'retryWrites=true&w=majority'
    # client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    # mongo_db=client.db
    # analyzer = DbAnalyzer(mongo_db)
    # analyzer.executeAndDiscard()

    ##test
    # from product_analyzer import ProductAnalyzer
    # DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
    #           f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
    #           'retryWrites=true&w=majority'
    # client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    # mongo_db=client.db
    
    # analyzer = DbAnalyzer(mongo_db)
    # analyzer.analyze()
    # f=open('mongoDB_errorCheck2.json','a')
    # f.write( json.dumps(analyzer.TEST_DuplicateList,indent='\t') )
    # f.close()


    # f=open('mongoDB_errorCheck.json','r')
    # data = json.loads( f.read() )
    # f.close()
    # duplicateList = []
    # for o in data:
    #     dateHashMap = {}
    #     i = 0
    #     for cO in o["data"]:
    #         if cO['date'] in dateHashMap:
    #             duplicateList.append({
    #                 "id":o['id'],
    #                 'index':i,
    #                 'date':cO['date']
    #             })
    #         else:
    #             dateHashMap[ cO['date'] ] = True
    #         i += 1
    # f=open('mongoDB_errorCheck_LOG.json','a')
    # f.write( json.dumps(duplicateList,indent='\t') )
    # f.close()
        
    # f=open('mongoDB_errorCheck_LOG.json','r')
    # deletionData = json.loads( f.read() )
    # f.close()
    # targetIds = []
    # hashMap = {}
    # for delObj in deletionData:
    #     targetIds.append( delObj['id'] )
    #     hashMap[ delObj['id'] ] = delObj
    # for dbItem in mongo_db.products.find({"id": {"$in": targetIds}},{"history":1,"id":1}):
    #     listOfElems = []
    #     for o in dbItem['history']:
    #         listOfElems.append( o['date'] )
    #     if len(listOfElems) == len(set(listOfElems)):
    #         print(f"Error detected! {dbItem['id']}")
    #         continue
    #     del dbItem['history'][ hashMap[ dbItem['id'] ]['index'] ]
    #     mongo_db.products.update_one({"id":dbItem['id']},{"$set":{"history":dbItem['history']}})
    #     print(f"Deletion executed on { dbItem['id'] } / index: { hashMap[ dbItem['id'] ]['index'] }")

    # f=open('.trash/2021-08-24.json','r')
    # data = json.loads( f.read() )
    # f.close()
    # f=open('.trash/2021-08-25.json','r')
    # push_data1 = json.loads( f.read() )
    # f.close()
    # f=open('.trash/2021-08-26.json','r')
    # push_data2 = json.loads( f.read() )
    # f.close()
    # data = data[0:6]
    # for item in data:
    #     for cItem in push_data1:
    #         if (item['id'] == cItem['id']):
    #             item['history'].insert(0, cItem['history'][0] )
    #     for cItem in push_data2:
    #         if (item['id'] == cItem['id']):
    #             item['history'].insert(0, cItem['history'][0] )
    # f=open('testUploadData.json','a')
    # f.write( json.dumps( data,indent='\t' ) )
    # f.close()
    
    # f=open('testUploadData.json','r')
    # data = json.loads( f.read() )
    # f.close()
    # mongo_db.deletionTest.insert_many(data)
    # i = 0
    # for item in mongo_db.deletionTest.find({},{"id":1,"history":1}):
    #     if (i == 3):
    #         i = 0
    #     #pull history
    #     del item['history'][i]
    #     mongo_db.deletionTest.update_one({"id":item['id']},{"$set":{"history":item['history']}})
    #     i += 1

    # mongoHandle = MongoDatabase()
    # mongoHandle.checkForDuplicatesAndFix()