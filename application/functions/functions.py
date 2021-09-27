from bson.json_util import dumps, loads
import json
from datetime import datetime, timedelta, date
from application import mongo_db
import math

def recurr_insertDbDataToHighlights(data,dbDataHashMap):
    for k, content in data.items():
        if isinstance(content,dict):
            content[k] = recurr_insertDbDataToHighlights(content,dbDataHashMap)
        elif isinstance(content,list):
            for item in content:
                if 'id' in item:
                    print('inserting to product:' + item['id'])
                    item["image"] = dbDataHashMap[ item['id'] ]["image"]
                    item["title"] = dbDataHashMap[ item['id'] ]["title"]
    return data
def recurr_pullIdsFromHighlights(data,carry = None):
    if not carry:
        carry = list()
    for k, content in data.items():
        if isinstance(content,dict):
            carry = recurr_pullIdsFromHighlights(content,carry)
        elif isinstance(content,list):
            for item in content:
                if 'id' in item:
                    carry.append(item['id'])
    return carry

def parseMongo(data,format='object'):
    list_cur = list(data)
    json_string = dumps(list_cur, indent = 2)
    json_data = json.loads(json_string)
    if not json_data:
        return 0 #"Product not found"
    if (format == 'object'):
        return json_data #json.loads(json_data)
    else: #string
        return json_string

def getProductsPage(ids,page,productsPerPage):
    
    startIndex = page*productsPerPage-productsPerPage
    endIndex = startIndex+productsPerPage
    myIds = ids[startIndex:endIndex]
    cursor = list()
    for item in mongo_db.products.find({"id": {"$in": myIds}},{"history": {"$slice": 1 }}):
        cursor.append(item)
    data = parseMongo(cursor)
    
    return data
    
def getCategoryIDs(categoryString):
    ids = list()
    cat = categoryString.replace("-", "/")
    for _id in mongo_db.products.find({"category_name_full_path" : {"$regex": f"^{ cat }"}}).distinct('id'):
        ids.append(_id)
    return ids

def getDbAge(products):
    for i in range(50):
        ckDate = datetime.now()-timedelta(days=i)
        ckDateString = ckDate.strftime("%Y-%m-%d")
        ck = products.find_one({'history.0.date':ckDateString},{'id':1})
        if ck:
            lastDay = ckDate
            _id = ck['id']
            break
    
    baseDate = products.find_one({'id':_id},{'id':1,"history": {"$slice": -1 }})
    baseDate = baseDate['history'][0]['date']
    array = baseDate.split('-')
    baseDate = datetime(int(array[0]),int(array[1]),int(array[2]))

    for i in range(1,50):
        ckDate = baseDate-timedelta(days=i)
        ckDateString = ckDate.strftime("%Y-%m-%d")
        ck = products.find_one({"history": {"$elemMatch": {"date": ckDateString}}},{"id":1})
        if not ck:
            # firstDay = ckDate+timedelta(days=1)
            firstDay = ckDate
            break
    
    delta = lastDay - firstDay
    return delta.days
    
        
def getProductPagination(data):
    pagination = list()
    
    pageRange = 5 if data['productCount'] >= 5*data['productsPerPage'] else data['productCount']/data['productsPerPage']
    if pageRange <= 1:
        return pagination
    pageRange = math.ceil(pageRange)
    
    startPage = 1 if (data['page'] <= 3) else data['page']-2
    pageUp = data['page'] + 1
    pageDown = 1 if data['page'] == 1 else data['page'] - 1

    for i in range(startPage,(startPage+pageRange)):
        current = True if (data['page'] == i) else None
        pagination.append({
            'text':i,
            'url':data['basePageUrl'] + str(i),
            'current':current
        })
        if (i == data['productsMaxPageCount']):
            break
    
    if (data['page'] > 1):
        pagination.insert(0,{
            'text':'«',
            'url':data['basePageUrl'] + str(pageDown),
            'current':0
        })
        if (data['page'] > 3):
            pagination.insert(0,{
                'text':'««  ',
                'url':data['basePageUrl'] + str(1),
                'current':0
            })

    if (data['page'] != data['productsMaxPageCount']):
        pagination.append({
            'text':'»',
            'url':data['basePageUrl'] + str(pageUp),
            'current':0
        })
    if (data['page'] < data['productsMaxPageCount']-2):
        pagination.append({
            'text':'  »»',
            'url':data['basePageUrl'] + str(data['productsMaxPageCount']),
            'current':0
        })
    return pagination

def appendDataToTableData(data,tableRangeMinimum):
    now = datetime.now()
    tableData = list()
    dataIndex = 0
    prices = list()
    for o in data:
        prices.append(o["price"])
    _min = min(prices)
    _max = max(prices)
    # print(data)
    d0 = date(int(data[0]['date'][0:4]),int(data[0]['date'][5:7]),int(data[0]['date'][8:10]))
    d1 = date(int(data[len(data)-1]['date'][0:4]),int(data[len(data)-1]['date'][5:7]),int(data[len(data)-1]['date'][8:10]))
    delta = d0 - d1
    span = delta.days+1
    colCount = tableRangeMinimum if (span < tableRangeMinimum) else span
    
    # self.dayRange = (delta.days)
    for i in range(colCount):
        ckDate = now + timedelta(days=-i)
        push = True
        highlight = None
        if (dataIndex < len(data)):
            array = data[dataIndex]['date'].split('-')
            itemDate = datetime(int(array[0]),int(array[1]),int(array[2]))
            if ( ckDate.strftime("%Y-%m-%d") == itemDate.strftime("%Y-%m-%d") ):
                push = False
        if push:
            tableData.append( {
                "date":ckDate.strftime("%Y-%m-%d"),
                "price":"n/a",
                "comparative_unit_price":"n/a",
                "active":"n/a",
                "highlight":highlight
            } )
        else:
            if (_max != _min):
                if (data[dataIndex]['price'] == _max):
                    highlight = "max"
                if (data[dataIndex]['price'] == _min):
                    highlight = "min"
            data[dataIndex]["highlight"] = highlight
            tableData.append( data[dataIndex] )
            dataIndex += 1
    return tableData

import unicodedata, re

# def getProductUrlLink(productObj):
#     text = str( productObj['title'] )
def getProductUrlLink(title):
    text = str( title )
    try:
        text = unicode(text, 'utf-8')
    except NameError:
        pass
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")
    text = str(text)
    text = text.replace('%',' proc ')
    text = re.sub('[^0-9a-zA-Z]+', '-', text)
    text = text.lower()
    text = text.rstrip('-')
    link = 'https://pagrindinis.barbora.lt/produktai/' + text # + '-' + productObj['id']
    return link

