from application import app, mongo_db, api
import os
from flask import render_template, request,json,abort # Response, jsonify, redirect, flash, url_for, session
from flask_restx import Resource
from datetime import date #, datetime, timedelta
import math
from application.scripts.functions import *
from application.scripts.product_analyzer import ProductAnalyzer



# if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
if True:
    disable_onLoad = False
    navData = {
        "productCount":0,
        "dbAge":0,
    }
    productsPerPage = 24
    
    if not disable_onLoad:
        ids = list()
        ids = mongo_db.products.find({},{"id":1}).distinct('id')
        
        navData["productCount"] = len(ids)
        navData["dbAge"] = getDbAge(mongo_db.products)
    
    dbStats_cursor = mongo_db.dbStatsDataFinal.find()
    dbStats = parseMongoCollection(dbStats_cursor,'list')
    dbStatsApiData = dict()
    for item in dbStats:
        dbStatsApiData[ item["date"] ] = item

    categoryCounts_cursor = mongo_db.categoryCounts.find_one()
    categoryCounts = parseMongoCollection(categoryCounts_cursor,'dict')

    categoryPathing_cursor = mongo_db.categoryPathing.find_one()
    categoryPathing = parseMongoCollection(categoryPathing_cursor,'dict')

    highlightsData_cursor = mongo_db.highlights.find_one()
    highlightsData = parseMongoCollection(highlightsData_cursor,'dict')

    # f=open( 'temp/categoryPathing.json','r' )
    # categoryPathing = json.loads(f.read())
    # f.close()
    # f=open( 'temp/categoryCounts.json','r' )
    # categoryCounts = json.loads(f.read())
    # f.close()
    # f = open('temp/dbStatsDataFinal.json','r')
    # dbStats = json.loads( f.read() )
    # f.close()
    # dbStatsApiData = dict()
    # for item in dbStats:
    #     dbStatsApiData[ item["date"] ] = item
    # f = open('temp/highlights.json','r')
    # string = f.read()
    # f.close()
    # highlightsData = json.loads( string )

## API ##
#################################
productAPIKeys = [
    'id',
    'title',
    'category_name_full_path',
    'root_category_id',
    'comparative_unit',
    'brand_name'
]
productAPIKeysString = ", ".join(productAPIKeys)
@api.route('/product',doc={"description": f"Returns product(s) with full history based on url parameters: {productAPIKeysString}.\nLimit 400 products per request.\n\nExample: product?brand_name=AROSO"})
class GetProduct(Resource):
    def get(self):
        needleParams = {}
        for k in productAPIKeys:
            value = request.args.get(k, None)
            if value:
                needleParams[k] = value
        try:
            results = mongo_db.products.find( needleParams ).limit(400)
        except Exception as e:
            abort(404,str(e))
        callBack = parseMongo(results)
        if isinstance(callBack,list):
            return callBack
        else:
            abort(401,"Product not found")

        
@api.route('/product-ids/',doc={"description": "Returns an array of product ids."})
class GetAllProducts(Resource):
    def get(self):
        ids = list()
        try:
            ids = mongo_db.products.find({},{"id":1})
        except Exception as e:
            abort(400,str(e))
        if not ids:
            abort(401,"Not Found")
        else:
            #removing '_id' object
            finalIds = []
            for item in ids:
                finalIds.append(item['id'])
            return finalIds

@api.route('/dailystats/<dateString>',doc={"description": "Returns following:\n -prices difference to average (diff_perc)\n -number of products available (count)\n -total number of products - same for any day (total)\n -percentage of products on the day (perCent)"})
@api.doc(params={'dateString': 'Use format yyyy-mm-dd'})
class GetDailyStats(Resource):
    def get(self,dateString):
        errorFlags = []
        if not dateString:
            errorFlags.append("Missing date. Use yyyy-mm-dd.")
        else:
            arr = dateString.split('-')
            if (len(arr) != 3) or (len(dateString) != 10):
                errorFlags.append(f"Incorrect date format: {dateString}. Use yyyy-mm-dd.")
            else:
                try:
                    _ = date(int(arr[0]),int(arr[1]),int(arr[2]))
                except:
                    errorFlags.append(f"Incorrect date format: {dateString}. Use yyyy-mm-dd.")
        if errorFlags:
            abort(400,'\n'.join(errorFlags))
        if dateString in dbStatsApiData:
            return dbStatsApiData[dateString]
        abort(404,f"Day {dateString} not found")
#################################

##ROUTES
##NAVIGATIONAL
highlightsCats = ["var_stdDev","var_perc","topToday","availability_perc"]
highlightsSubCats = ["tops","lows"]
@app.route("/")
@app.route("/index")
@app.route("/home")
def index():
    targetIds = recurr_pullIdsFromHighlights(highlightsData)
    dbPull = mongo_db.products.find({"id": {"$in": targetIds}},{"id":1,"image":1,"title":1},batch_size=len(targetIds))
    dbPull = list(dbPull)
    hashMap = dict()
    for product in dbPull:
        hashMap[ product['id'] ] = {
            "image":product['image'],
            "title":product['title']
        }
    for cat in highlightsCats:
        for subCat in highlightsSubCats:
            for product in highlightsData[cat][subCat]:
                product["image"] = hashMap[ product['id'] ]["image"]
                product["title"] = hashMap[ product['id'] ]["title"]
                product["link"] = getProductUrlLink(product["title"])
    
    roundKeys = ['diff_perc','perCent']
    for o in dbStats:
        for k, v in o.items():
            if k in roundKeys:
                if not isinstance(v,str):
                    o[k] = round(float(v),4)

    pieChartData = categoryCounts
    activePage={
        "link":"index",
        "label":"Home"
    }
    # return render_template("index.html",activePage=activePage,navData=navData,pieChartData=pieChartData,data=highlightsData,graphData=dbStats, index=True)
    return render_template("index.html",activePage=activePage,navData=navData,pieChartData=pieChartData,data=highlightsData,graphData=dbStats)


@app.route("/products")
def products():
    data = list()
    page = request.args.get('page', None)
    cat = request.args.get('cat', None)
    
    q = request.args.get('q', None)
    
    page = 1 if (page == None) else int(page)
    basePageUrl = '/products?'
    ## retreiving product data
    if q:
        q = q.strip()
        targetIds = mongo_db.products.find({"title":{"$regex" : q, "$options":"i"}},{"id":1}).distinct('id')
        targetIds = list(targetIds)
        if not targetIds:
            Message404 = f"No matches found for \"{q}\"."
            return render_template("404.html",navData=navData,Message404=Message404)
        basePageUrl += 'q=' + q + '&page=' if len(targetIds) > productsPerPage else 'page='
    else:
        targetIds = getCategoryIDs(cat) if cat else ids
        basePageUrl += 'cat=' + cat + '&page=' if cat else 'page='
    
    productsMaxPageCount = math.ceil(len(targetIds)/productsPerPage)
    data = getProductsPage(targetIds,page,productsPerPage)
    for productObj in data:
        productObj["link"] = getProductUrlLink(productObj["title"])
        productObj["analyzeLink"] = '/analyze?id=' + productObj['id']
        productObj["imageLarge"] = productObj["image"][0:-5] + "m.png"
    
    paginationSubmit = dict({
        "page":page,
        "basePageUrl":basePageUrl,
        "productsMaxPageCount":productsMaxPageCount,
        "productCount":int(len(targetIds)),
        "productsPerPage":productsPerPage
    })
    pagination = getProductPagination(paginationSubmit)
    
    catArr = cat.split('-') if cat else []
    activePage={
        "link":"products",
        "label":"Products"
    }
    # return render_template("products.html",activePage=activePage,navData=navData, catArr = catArr,categories=categoryPathing, pagination=pagination, data=data, products=True)
    return render_template("products.html",activePage=activePage,navData=navData, catArr = catArr,categories=categoryPathing, pagination=pagination, data=data)

@app.route("/about")
def about():
    tableTestData = list()
    for i in range (20):
        line = dict()
        for ci in range(4):
            line[f'key_h{ci}'] = str(f"data_{i}_{ci}")
        tableTestData.append(line)
    activePage={
        "link":"about",
        "label":"About"
    }
    # print( json.dumps(tableTestData,indent='\t') )
    # return render_template("about.html",activePage=activePage,tableTestData=tableTestData,navData=navData,about=True)
    return render_template("about.html",activePage=activePage,tableTestData=tableTestData,navData=navData)
    
##SUBMITS
@app.route('/analyze')
def analyze_product():
    product_id = request.args.get('id', None)
    if not product_id:
        Message404 = "No product ID submitted."
        return render_template("404.html",navData=navData,Message404=Message404)
    
    data = mongo_db.products.find_one({"id":product_id})
    if not data:
        Message404 = f"Product ID {product_id} not found."
        return render_template("404.html",navData=navData,Message404=Message404)
    
    graphData = {
        "data":data['history'],
        "title":data['title'],
        "img":data["image"][0:-5] + "m.png"
    }
    productHandle = ProductAnalyzer(data['history'])
    analyzeResults = productHandle.getResultsAsDict()
    link = getProductUrlLink(data["title"])
    graphData["tableData"] = appendDataToTableData(data['history'],26)
    graphData["descriptiveTableData"] = [
        {
            "title":"Title",
            "value":data["title"],
            "link":link
        },
        {
            "title":"Brand Name",
            "value":data["brand_name"] if data["brand_name"] else "N/A"
        },
        {
            "title":"Comparative Unit",
            "value":data["comparative_unit"]
        },
        {
            "title":"Mean",
            "value":"€ " + str(round(productHandle.mean,2))
        },
        {
            "title":"Standard Deviation",
            "value":"€ " + str(round(analyzeResults["var_stdDev"],2))
        },
        {
            "title":"Volatility",
            "value":str(round(analyzeResults["var_perc"],2)) + "%"
        },
        {
            "title":"Availability",
            "value":str(round(analyzeResults["availability_perc"],2)) + "%"
        }
    ]
    activePage={
        "link":"products",
        "label":"Products"
    }
    return render_template("analyze.html",activePage=activePage,navData=navData, graphData=graphData)
