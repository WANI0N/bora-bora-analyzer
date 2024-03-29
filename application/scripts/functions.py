from bson.json_util import dumps #, loads
import json
from datetime import datetime, timedelta, date
from email_validator import validate_email, EmailNotValidError
# from application import AES
import urllib, string, secrets
try:
    from application import mongo_db
except:
    ## for testing
    import certifi
    ca = certifi.where()
    import os, pymongo
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL=f'mongodb+srv://user:{os.environ.get("DB_PASSWORD")}'\
              f'@cluster0.zgmnh.mongodb.net/{os.environ.get("DB_NAME")}?'\
              'retryWrites=true&w=majority'
    client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    mongo_db=client.db
import math

def get_daycount_subtract_dates(datestring1: str, datestring2: str) -> int:
    d0 = convert_date_string_to_obj(datestring1)
    d1 = convert_date_string_to_obj(datestring2)
    return (d0 - d1).days

def calculate_day(date_string: str, diff: int) -> datetime:
    array = date_string.split("-")
    date = datetime(int(array[0]), int(array[1]), int(array[2]))
    next_date = date+timedelta(days=diff)
    return next_date.strftime("%Y-%m-%d")  

def convert_date_string_to_obj(input_date: str) -> datetime:
    array = input_date.split("-")
    return datetime(int(array[0]), int(array[1]), int(array[2]))

def get_date_range(end_date: str, start_date: str) -> list:
    output = []
    ed_obj = convert_date_string_to_obj(end_date)
    sd_obj = convert_date_string_to_obj(start_date)
    current_date = ed_obj
    while current_date:
        output.append(current_date.strftime("%Y-%m-%d"))
        if current_date == sd_obj:
            current_date = ""
            continue
        current_date = current_date-timedelta(days=1)
    return output

def convert_products_to_old_format(products: list) -> list:
    for product in products:
        if 'history' not in product:
            return []
        product['history'] = convert_history_to_old_format(product['history'])
    return products

def convert_history_to_old_format(input_history: list) -> list:
    output = []
    for item in input_history:
        if item['end-date'] == item['start-date']:
            output.append({
                'price': item['price'],
                'comparative_unit_price': item['comparative_unit_price'],
                'date': item['end-date'],
                'active': item['availability'][0],
            })
            continue
        date_range = get_date_range(item['end-date'], item['start-date'])
        for i, date in enumerate(date_range):
            # print(f"i={i} availability={item['availability']}")
            output.append({
                'price': item['price'],
                'comparative_unit_price': item['comparative_unit_price'],
                'date': date,
                'active': item['availability'][i],
            })
    return output

def recurr_insertDbDataToHighlights(data,dbDataHashMap):
    for k, content in data.items():
        if isinstance(content,dict):
            content[k] = recurr_insertDbDataToHighlights(content,dbDataHashMap)
        elif isinstance(content,list):
            for item in content:
                if 'id' in item:
                    item["image"] = dbDataHashMap[ item['id'] ]["image"]
                    item["title"] = dbDataHashMap[ item['id'] ]["title"]
    return data
def recurr_pullIdsFromHighlights(data,carry = None):
    """extracts product ids from nested object

    Args:
        data (object): highlightsData
        carry (string, optional): Do not submit (used for recurrsion carry list). Defaults to None.

    Returns:
        [list]: list of products
    """
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

def parseMongoCollection(cursorData, type):
    if (type == "list"):
        data = list(cursorData)
        for item in data:
            del item["_id"]
    elif (type == "dict"):
        data = dict(cursorData)
        del data["_id"]
    else:
        return "Missing type"
    return data

def getProductsPage(ids,page,productsPerPage):
    """get visible product data (limit per page)

    Args:
        ids (list): product ids needed (can be all)
        page (integer): pagination page number (determines which products are retreived)
        productsPerPage (integer): number of products retreived

    Returns:
        [list]: product data (sliced to latest date per product)
    """
    startIndex = page*productsPerPage-productsPerPage
    endIndex = startIndex+productsPerPage
    myIds = ids[startIndex:endIndex]
    cursor = list()
    for item in mongo_db.products.find({"id": {"$in": myIds}},{"history": {"$slice": 1 }}):
        cursor.append(item)
    data = parseMongo(cursor)
    
    return data
    
def getCategoryIDs(categoryString):
    """get product ids of specific category and child categories

    Args:
        categoryString (string): submit with dash(-) separator

    Returns:
        [list]: product ids
    """
    ids = list()
    cat = categoryString.replace("-", "/")
    for _id in mongo_db.products.find({"category_name_full_path" : {"$regex": f"^{ cat }"}}).distinct('id'):
        ids.append(_id)
    return ids

# def getDbAge(products):
#     for i in range(50):
#         ckDate = datetime.now()-timedelta(days=i)
#         ckDateString = ckDate.strftime("%Y-%m-%d")
#         # ck = products.find_one({'history.0.date':ckDateString},{'id':1})
#         ck = products.find_one({'history.0.end-date': ckDateString},{'id':1})
#         if ck:
#             lastDay = ckDate
#             _id = ck['id']
#             break
    
#     baseDate = products.find_one({'id':_id},{'id':1,"history": {"$slice": -1 }})
#     # baseDate = baseDate['history'][0]['date']
#     baseDate = baseDate['history'][0]['start-date']
#     array = baseDate.split('-')
#     baseDate = datetime(int(array[0]),int(array[1]),int(array[2]))

#     for i in range(1,50):
#         ckDate = baseDate-timedelta(days=i)
#         ckDateString = ckDate.strftime("%Y-%m-%d")
#         # ck = products.find_one({"history": {"$elemMatch": {"date": ckDateString}}},{"id":1})
#         ck = products.find_one({"history": {"$elemMatch": {"start-date": ckDateString}}},{"id":1})
#         if not ck:
#             # firstDay = ckDate+timedelta(days=1)
#             firstDay = ckDate
#             break
#     delta = lastDay - firstDay
#     return delta.days

class URL_parser:
    def __init__(self,AES):
        """encodes and decodes url paramater submits

        Args:
            AES (class): AES encryption class
        """
        self.AES = AES
    def encode(self,input):
        """encodes and encrypts (with salt) data to valid url string

        Args:
            input (string, list, dict): any

        Returns:
            encoded and encrypted string
        """
        if not isinstance(input,str):
            if isinstance(input,int):
                input = str(input)
            elif isinstance(input,list) or isinstance(input,dict):
                input = json.dumps(input)
        salt = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(3))
        encr = self.AES.encrypt( salt + input )
        return urllib.parse.quote_plus(encr)
    def decode(self,input):
        """decodes and decrypts

        Args:
            input (string)

        Returns:
            [any]: decoded content
        """
        decode = urllib.parse.unquote(input)
        decode = self.AES.decrypt(decode)
        decode = decode[3::]
        try:
            return json.loads( decode )
        except:
            return decode


def validateEmailFormat(email):
    status = {"valid":True}
    try:
        # Validate.
        valid = validate_email(email)
        # Update with the normalized form.
        status['email'] = valid.email
    except EmailNotValidError as e:
        # email is not valid, exception message is human-readable
        status['valid'] = False
        status['reason'] = str(e)
    return status

def validatePasswordFormat(passwd):
    """validates password strength

    Args:
        passwd (string): any

    Returns:
        [dict]: valid:boolean, reason:list
    """
    SpecialSym =['$','@','#','%','-','?',',','\\','.','!','^','&','\"','>','<','~',':',':']
    status = {
        "valid":False,
        "reason":[]
    }
    if len(passwd) < 6:
        status['reason'].append('Password length should be at least 6')
    if len(passwd) > 50:
        status['reason'].append('Password length should be not be greater than 50')
    if not any(char.isdigit() for char in passwd):
        status['reason'].append('Password should have at least one numeral')
    if not any(char.isupper() for char in passwd):
        status['reason'].append('Password should have at least one uppercase letter')
    if not any(char.islower() for char in passwd):
        status['reason'].append('Password should have at least one lowercase letter')
    if not any(char in SpecialSym for char in passwd):
        status['reason'].append(f"Password should have at least one of the symbols: {''.join(SpecialSym)}")
    if not status['reason']:
        status['valid'] = True
    return status

def getProductPagination(data):
    """get a list of pagination button data (link, innerText, highlight)

    Args:
        data (custom object): current page, basePageUrl, productsMaxPageCount, productCount, productsPerPage

    Returns:
        [list]: pagination button data
    """
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
    """modifies product data to table data, empty days padded with 'n/a'

    Args:
        data (list): product's history list
        tableRangeMinimum (integer): number large enough to have scrollable table

    Returns:
        [list]: tableData
    """
    now = datetime.now()
    tableData = list()
    prices = list()
    hashMap = dict()
    for o in data:
        prices.append(o["price"])
        hashMap[o["date"]] = o
    _min = min(prices)
    _max = max(prices)
    array = now.strftime("%Y-%m-%d").split('-')
    d0 = date(int(array[0]),int(array[1]),int(array[2]))
    d1 = date(int(data[len(data)-1]['date'][0:4]),int(data[len(data)-1]['date'][5:7]),int(data[len(data)-1]['date'][8:10]))
    delta = d0 - d1
    span = delta.days+1
    colCount = tableRangeMinimum if (span < tableRangeMinimum) else span
    # self.dayRange = (delta.days)
    for i in range(colCount):
        ckDate = now + timedelta(days=-i)
        ckDateString = ckDate.strftime("%Y-%m-%d")
        highlight = None
        if ckDateString in hashMap:
            pushObject = hashMap[ckDateString]
            if (_max != _min):
                if (pushObject['price'] == _max):
                    highlight = "max"
                if (pushObject['price'] == _min):
                    highlight = "min"
            pushObject["highlight"] = highlight
            tableData.append( pushObject )
        else:
            tableData.append( {
                "date":ckDate.strftime("%Y-%m-%d"),
                "price":"n/a",
                "comparative_unit_price":"n/a",
                "active":"n/a",
                "highlight":highlight
            } )
        
    return tableData

import unicodedata, re

def get_product_url_link(title):
    """converts product title to barbora url

    Args:
        title (string): product title

    Returns:
        string: full url
    """
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

