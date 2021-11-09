from werkzeug.datastructures import Headers
from application import app, mongo_db, api, server_mail
import os
# import random
# import requests
# from flask_mail import Message
from flask import render_template, request,abort,make_response,redirect # Response,json , jsonify, flash, url_for, session
from flask_restx import Resource
from datetime import date, datetime, timedelta
import math
from application.scripts.functions import *
from application.scripts.product_analyzer import ProductAnalyzer
from application.scripts.user import User

from application import server_mail

from application.scripts.API_limiter import API_Limiter

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "500 per hour"]
)
# set localEnvironment and activate if statement: os.environ.get("WERKZEUG_RUN_MAIN") to run only once for local host
# localEnvironment = True
localEnvironment = False
# if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
if True:
    userLoginStatus = False
    
    footerData = {
        "productCount":0,
        "dbAge":0,
    }
    productsPerPage = 24
    
    from application import AES

    users = User(mongo_db.user,server_mail,AES)
    users.cleanUp()
    urlParser = URL_parser(AES)

    API_limiter = API_Limiter()

    ids = list()
    ids = mongo_db.products.find({},{"id":1}).distinct('id')
    
    footerData["productCount"] = len(ids)
    footerData["dbAge"] = getDbAge(mongo_db.products)
    
    if localEnvironment:
        # load from local temp file (data can be manually generated in db_analyzer.py)
        f = open('temp/dbStatsDataFinal.json','r')
        dbStats = json.loads( f.read() )
        f.close()
        dbStatsApiData = dict()
        for item in dbStats:
            dbStatsApiData[ item["date"] ] = item
        
        f=open( 'temp/categoryCounts.json','r' )
        categoryCounts = json.loads(f.read())
        f.close()
        
        f=open( 'temp/categoryPathing.json','r' )
        categoryPathing = json.loads(f.read())
        f.close()
        
        f = open('temp/highlights.json','r')
        string = f.read()
        f.close()
        highlightsData = json.loads( string )
    else:
        # production, load from db
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
    

## API ##
#################################
# public API endpoints
productAPIKeys = [
    'id',
    'title',
    'category_name_full_path',
    'root_category_id',
    'comparative_unit',
    'brand_name'
]
productAPIKeysString = ", ".join(productAPIKeys)
@api.route('/product',doc={"description": f"Returns product(s) with full history based on url parameters: {productAPIKeysString}.\nLimit 400 products per request.\n\nRate limit: 15/min\n\nExample: product?brand_name=AROSO"})
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
        for prod in callBack:
            del prod["_id"]
        if isinstance(callBack,list):
            return callBack
        else:
            abort(401,"Product not found")

        
@api.route('/product-ids/',doc={"description": "Returns an array of all product ids.\n\nRate limit: 1/min"})
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

@api.route('/dailystats/<dateString>',doc={"description": "Returns following:\n -prices difference to average (diff_perc)\n -number of products available (count)\n -total number of products - same for any day (total)\n -percentage of products on the day (perCent)\n\nRate limit: 15/min"})
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
# API endpoints used for dynamic page actions (no reload needed)
@api.route('/validation-email/',doc=False)
class SendValidationEmail(Resource):
    def post(self):
        data = api.payload
        if not data['token']:
            abort(405,"Missing Token")
        
        user = users.validateOneTimeToken(data['token'],"sendEmailValidation")
        if not user:
            abort(401,"Unauthorized")
        status = users.sendValidationEmail(user["email"])
        
        return {"emailSentStatus":status}

@api.route('/addAlert/',doc=False) # adding product to alerts
class AddAlert(Resource):
    def post(self):
        data = api.payload
        user = users.validateOneTimeToken(data['token'],"addAlert")
        if not user:
            abort(401,"Unauthorized")
        if 'innitial_state' not in data:
            abort(405,"Invalid Request")
        if data['product_id'] not in ids:
            abort(405,"Invalid Request")

        status = users.addAlert(user["id_cookie"],data['product_id'],data['innitial_state'])
        callBackData = {"addAlertStatus":status}
        if (len(data['product_id']) >= users.alertLimit):
            callBackData["reason"] = "Alert Limit Reached"
        return callBackData

@api.route('/submitAlerts/',doc=False)
class SubmitAlerts(Resource):
    def post(self):
        data = api.payload
        user = users.validateOneTimeToken(data['token'],"submitAlerts")
        if not user:
            abort(401,"Unauthorized")
        for item in data["alerts"]:
            if item['productID'] not in ids:
                abort(405,"Invalid request")
        status = users.updateAlerts(user["id_cookie"],data["alerts"])
        return {"submitAlertsStatus":status}
#################################


@app.before_request
def before_request():
    if not API_limiter.submit(request.remote_addr,request.url,request.method):
        return json.dumps({
            "error:":"Limit reached.",
            "IP":request.remote_addr,
        })
    # Force https, does not work for local host
    if not localEnvironment:
        if not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)

##ROUTES
##NAVIGATIONAL
highlightsCats = ["var_stdDev","var_perc","topToday","availability_perc"]
highlightsSubCats = ["tops","lows"]
@app.route("/")
@app.route("/index")
@app.route("/home")
def index():
    # get product ids from current highlights
    targetIds = recurr_pullIdsFromHighlights(highlightsData)
    # pull products (image and title needed)
    dbPull = mongo_db.products.find({"id": {"$in": targetIds}},{"id":1,"image":1,"title":1},batch_size=len(targetIds))
    dbPull = list(dbPull)
    # create hashmap for easier recall
    hashMap = dict()
    for product in dbPull:
        hashMap[ product['id'] ] = {
            "image":product['image'],
            "title":product['title']
        }
    # insert and ammend data for final table view
    for cat in highlightsCats:
        for subCat in highlightsSubCats:
            for product in highlightsData[cat][subCat]:
                product["image"] = hashMap[ product['id'] ]["image"]
                product["title"] = hashMap[ product['id'] ]["title"]
                product["trimedTitle"] = product["title"][0:35]
                if (len( product["trimedTitle"] ) == 35):
                    product["trimedTitle"] += "..."
                product["link"] = getProductUrlLink(product["title"])
                product["analyzeLink"] = "/analyze?id=" + product['id']
    

    pieChartData = categoryCounts
    cookie_id = request.cookies.get('userID')
    userLoginStatus = users.validateUserCookie(cookie_id)
    activePage={
        "link":"index",
        "label":"Home",
        "login":userLoginStatus
    }
    
    return render_template("index.html",activePage=activePage,footerData=footerData,pieChartData=pieChartData,data=highlightsData,graphData=dbStats)


@app.route("/products")
def products():
    data = list()
    page = request.args.get('page', None)
    cat = request.args.get('cat', None)
    q = request.args.get('q', None)
    cookie_id = request.cookies.get('userID')
    userLoginStatus = users.validateUserCookie(cookie_id)
    activePage={
        "link":"products",
        "label":"Products",
        "login":userLoginStatus
    }
    page = 1 if (page == None) else int(page)
    basePageUrl = '/products?'
    ## retreiving product data q=search query, 
    if q:
        q = q.strip()
        targetIds = mongo_db.products.find({"title":{"$regex" : q, "$options":"i"}},{"id":1}).distinct('id')
        targetIds = list(targetIds)
        if not targetIds:
            Message404 = f"No matches found for \"{q}\"."
            return render_template("404.html",activePage=activePage,footerData=footerData,Message404=Message404)
        basePageUrl += 'q=' + q + '&page=' if len(targetIds) > productsPerPage else 'page='
    else:
        targetIds = getCategoryIDs(cat) if cat else ids
        basePageUrl += 'cat=' + cat + '&page=' if cat else 'page='
    # get pagination last page
    productsMaxPageCount = math.ceil(len(targetIds)/productsPerPage)
    # get product data, only visible retreived
    data = getProductsPage(targetIds,page,productsPerPage)
    for productObj in data:
        productObj["link"] = getProductUrlLink(productObj["title"])
        productObj["analyzeLink"] = '/analyze?id=' + productObj['id']
        productObj["imageLarge"] = productObj["image"][0:-5] + "m.png"
    # get final pagination data
    paginationSubmit = dict({
        "page":page,
        "basePageUrl":basePageUrl,
        "productsMaxPageCount":productsMaxPageCount,
        "productCount":int(len(targetIds)),
        "productsPerPage":productsPerPage
    })
    pagination = getProductPagination(paginationSubmit)
    # catArr needed for view/highlight current categories
    catArr = cat.split('-') if cat else []
    
    return render_template("products.html",activePage=activePage,footerData=footerData, catArr = catArr,categories=categoryPathing, pagination=pagination, data=data)

@app.route("/login",methods = ['GET', 'POST'])
@limiter.limit("10/minute")
def login():
    # rc - reason code - list of possible user messages, encrypted url parameter
    rc = request.args.get('rc', None)
    displayMessages = urlParser.decode(rc) if rc else [] 
        
    ##login does not appear unless user is not logged in
    cookie_id = request.cookies.get('userID')
    userLoginStatus = users.validateUserCookie(cookie_id)
    activePage={
        "login":userLoginStatus
    }
    return render_template("login.html",displayMessages=displayMessages,activePage=activePage,footerData=footerData)

@app.route("/updatePassword",methods = ['GET', 'POST'])
def updatePassword():
    cookie_id = request.cookies.get('userID')
    userLoginStatus = users.validateUserCookie(cookie_id)
    errorMessages = []
    if not userLoginStatus:
        return redirect("/index")
    # GET method displays default reset pwd ui if validated cookie
    if request.method == "POST":
        # form POST for password reset
        current_pwd = request.form.get('current_pwd')
        new_pwd1 = request.form.get('new_pwd1')
        new_pwd2 = request.form.get('new_pwd2')
        if (new_pwd1 != new_pwd2):
            errorMessages.append( "New password was not inserted identically." )
        pwdStatus = validatePasswordFormat(new_pwd1)
        if not pwdStatus['valid']:
            errorMessages.extend(pwdStatus['reason'])
        if not errorMessages:
            status = users.updatePassword(cookie_id,current_pwd,new_pwd1)
            if status['success'] == True:
                rc = urlParser.encode( ['Your password has been reset, please login with your new password.'] )
                resp = make_response(redirect(f"/login?rc={rc}")) 
                resp.set_cookie('userID', '', expires=0) #remove cookie from user's browser
                return resp
            else:
                errorMessages.append( status['reason'] )
    
    activePage={
        "login":userLoginStatus
    }
    return render_template("updatePassword.html",errorMessages=errorMessages,activePage=activePage,footerData=footerData)
    

@app.route("/profile",methods = ['GET', 'POST'])
@limiter.limit("20/minute")
def profile():
    cookie_id = request.cookies.get('userID')
    userLoginStatus = users.validateUserCookie(cookie_id)
    if request.method == "GET": #normal click on profile
        if not userLoginStatus:
            return redirect("/login")
        deleteUser = request.args.get('deleteProfile', None)
        logOutUser = request.args.get('logoutProfile', None)
        if (deleteUser == "execute"):
            users.delete(cookie_id)
            rc = urlParser.encode( ['Your profile has been deleted.'] )
            return redirect(f"/login?rc={rc}")
        if (logOutUser == "execute"):
            users.logOut(cookie_id) #reset cookie id in db
            resp = make_response(redirect("/index")) 
            resp.set_cookie('userID', '', expires=0) #remove cookie from user's browser
            return resp
        
    else: #POST coming from login/create form
        email = request.form.get('uemail')
        password = request.form.get('pwd')
        login = request.form.get('login') #true/None
        create = request.form.get('create') #true/None
        email = email if email else None
        if not API_limiter.loginAttemptSubmit(request.remote_addr,email):
            return {"status":403,"message":"Too many attempts - forbidden"}
        remember = request.form.get('remember') #on/None
        if login == 'true':
            if users.validateUser(email,password):
                resp = make_response(redirect("/profile"))
                cookieId = users.getUserCookie(email)
                
                if remember == 'on':
                    resp.set_cookie('userID', cookieId,expires=datetime.now()+timedelta(days=9999),secure=True,httponly=True)
                else:
                    resp.set_cookie('userID', cookieId,secure=True,httponly=True)                
                return resp
            else:
                rc = urlParser.encode( ['Email or password are incorrect.'] )
                return redirect(f"/login?rc={rc}")
        if create == 'true':
            # form validation
            formInvalidReason = []
            emailStatus = validateEmailFormat(email)
            if not emailStatus['valid']:
                formInvalidReason.append(emailStatus['reason'])
            pwdStatus = validatePasswordFormat(password)
            if not pwdStatus['valid']:
                formInvalidReason.extend(pwdStatus['reason'])
            if formInvalidReason:
                rc = urlParser.encode( formInvalidReason )
                return redirect(f"/login?rc={rc}")

            status = users.create(email,password)
            if status:
                cookieId = users.getUserCookie(email)
                resp = make_response(redirect("/profile"))
                if remember == 'on':
                    resp.set_cookie('userID', cookieId,expires=datetime.now()+timedelta(days=9999),secure=True,httponly=True)
                else:
                    resp.set_cookie('userID', cookieId,secure=True,httponly=True)                
                users.sendValidationEmail(email)
                return resp
            else:
                rc = urlParser.encode( ['This account already exist.'] )
                return redirect(f"/login?rc={rc}")
        
    activePage={
        "link":"profile",
        "label":"Profile",
        "login":userLoginStatus
    }
    user = users.getUserByCookie(cookie_id)
    profileViewData = {
        "emailValidated":user["validation_status"],
        "email":user["email"]
    }
    # jsPayload must never contain user cookie in unencrypted form
    jsPayload = {}
    if not profileViewData["emailValidated"]:
        token = users.setOneTimeToken(cookie_id,"sendEmailValidation")
        jsPayload = {"tmp_token":token}
    else:
        token = users.setOneTimeToken(cookie_id,"submitAlerts")
        jsPayload = {"tmp_token":token}
        
    userAlerts = users.getAlerts(cookie_id)
    #update user data
    for alert in userAlerts:
        product = mongo_db.products.find_one({"id":alert['productID']},{"image":1,"title":1})
        alert["title"] = product["title"]
        alert["image"] = product["image"]
    
    
    profileViewData["alerts"] = userAlerts

    return render_template("profile.html",jsPayload=jsPayload,profileViewData=profileViewData,activePage=activePage,footerData=footerData)
    
##SUBMITS
@app.route('/analyze')
def analyze_product():
    cookie_id = request.cookies.get('userID')
    userLoginStatus = users.validateUserCookie(cookie_id)
    activePage={
        # "link":"products",
        # "label":"Products",
        "login":userLoginStatus
    }
        
    product_id = request.args.get('id', None)
    if not product_id:
        Message404 = "No product ID submitted."
        return render_template("404.html",activePage=activePage,footerData=footerData,Message404=Message404)
    jsPayload = {}
    if userLoginStatus:
        token = users.setOneTimeToken(cookie_id,"addAlert")
        jsPayload = {"tmp_token":token,"product_id":product_id}

    data = mongo_db.products.find_one({"id":product_id})
    if not data:
        Message404 = f"Product ID {product_id} not found."
        return render_template("404.html",activePage=activePage,footerData=footerData,Message404=Message404)
    
    pageData = {
        "data":data['history'],
        "title":data['title'],
        "img":data["image"][0:-5] + "m.png" # large img file name ends with 'm' instead of 's' in url
    }
    productHandle = ProductAnalyzer(data['history'])
    analyzeResults = productHandle.getResultsAsDict()
    link = getProductUrlLink(data["title"])
    pageData["tableData"] = appendDataToTableData(data['history'],26)
    pageData["title"] = data["title"]
    pageData["descriptiveTableData"] = [
        {
            "title":"Brand Name",
            "value":data["brand_name"] if data["brand_name"] else "N/A",
            "link":link
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
    
    return render_template("analyze.html",jsPayload=jsPayload,activePage=activePage,footerData=footerData, graphData=pageData)

@app.route("/password-reset",methods = ['GET', 'POST'])
@limiter.limit("5/minute")
def passwordReset():
    formData = {}
    formData['userMessages'] = []
    if request.method == 'GET':
        reset_code = request.args.get('reset_code', None)
        if reset_code:
            cookie_id = users.verifyPasswordResetSubmit(reset_code)
            # cookie_id = True
            if not cookie_id:
                rc = urlParser.encode( ['The password reset link is not valid. Click Forgot password to generate a new one.'] )
                return redirect(f"/login?rc={rc}")
            else:
                formData['userMessages'] = ['Please insert new password']
                token = users.setOneTimeToken(cookie_id,"submitNewPassword")
                formData['formToken'] = token
                formData['renderType'] = 'submitNewPassword'
        else:
            formData['renderType'] = 'submitSendEmail'
    if request.method == 'POST':
        submitSendEmail = request.form.get('submitSendEmail') #true/None
        if submitSendEmail:
            email = request.form.get('submitEmail')
            emailStatus = validateEmailFormat(email)
            formData['renderType'] = 'submitSendEmail'
            if not emailStatus['valid']:
                formData['userMessages'].append(emailStatus['reason'])
            else:
                if users.getUserCookie( emailStatus['email'] ):
                    users.sendPasswordResetEmail(emailStatus['email'])
                formData['userMessages'].append('Email Password reset has been sent, please check your email address.')
        submitNewPassword = request.form.get('submitNewPassword') #true/None
        if submitNewPassword:
            new_pwd1 = request.form.get('new_pwd1')
            new_pwd2 = request.form.get('new_pwd2')
            if (new_pwd1 != new_pwd2):
                formData['userMessages'].append( "New password was not inserted identically." )
            pwdStatus = validatePasswordFormat(new_pwd1)
            if not pwdStatus['valid']:
                formData['userMessages'].extend(pwdStatus['reason'])
            if formData['userMessages']:
                formData['formToken'] = request.form.get('formToken')
                formData['renderType'] = 'submitNewPassword'
            if not formData['userMessages']:
                if users.resetPassword(request.form.get('formToken'),new_pwd1):
                    rc = urlParser.encode( ['Your password has been reset, please login with your new password.'] )
                    return redirect(f"/login?rc={rc}")
                else:
                    formData['renderType'] = 'submitSendEmail'
                    formData['userMessages'].append( "Something went wrong, please submit a new reset password request." )

    cookie_id = request.cookies.get('userID')
    userLoginStatus = users.validateUserCookie(cookie_id)
    activePage={
        "login":userLoginStatus
    }
    return render_template('resetPassword.html',formData=formData,activePage=activePage,footerData=footerData)

@app.route("/email-validation/<validation_code>")
@limiter.limit("5/minute")
def emailValidation(validation_code):
    status = users.validateUserEmail(validation_code)
    cookie_id = request.cookies.get('userID')
    userLoginStatus = users.validateUserCookie(cookie_id)
    
    if not status:
        Message404 = "Unfortunately it has not been possible to validate email. If you haven't validated your email within 48h, your account is automatically deleted. Please create an account again."
        activePage={
            "login":userLoginStatus
        }
        return render_template("404.html",activePage=activePage,footerData=footerData,Message404=Message404)
    return redirect("/profile")

@app.route("/unsubscribe",methods = ['GET', 'POST'])
def unsubscribe():
    formData = {}
    formData["userMessages"] = []
    if request.method == 'GET':
        token = request.args.get('token', None)
        Message404 = ""
        if not token:
            Message404 = "Missing token"
        elif not users.checkUnsubToken(token):
            Message404 = "Invalid token"
        if Message404:
            cookie_id = request.cookies.get('userID')
            activePage={"login":users.validateUserCookie(cookie_id)}
            return render_template("404.html",activePage=activePage,footerData=footerData,Message404=Message404)
        formData['formToken'] = token
    else: #POST
        unsubToken = request.form.get('formToken')
        unsubscribe = request.form.get('unsubscribe') #true/None
        
        deactivate = request.form.get('deactivate') #on/None
        remove = request.form.get('remove') #on/None
        deactivate = True if (deactivate == 'on') else False
        remove = True if (remove == 'on') else False
        if not unsubToken:
            formData["userMessages"].append('Invalid token.')
        if not deactivate and not remove:
            formData["userMessages"].append('No action taken.')
        if not formData["userMessages"]:
            if unsubToken:
                if unsubscribe:
                    status = users.unsubscribeUser(unsubToken,deactivate,remove)
            if status:
                if remove:
                    formData["userMessages"].append('All alerts have been deleted.')
                elif deactivate:
                    formData["userMessages"].append('All alerts have been deactivated.')
            else:
                formData["userMessages"].append('Invalid token.')
    
    return render_template("unsubscribe.html",formData=formData)

@app.route("/about")
def about():
    cookie_id = request.cookies.get('userID')
    userLoginStatus = users.validateUserCookie(cookie_id)
    activePage={
        "link":"about",
        "label":"About",
        "login":userLoginStatus
    }
    
    return render_template("about.html",activePage=activePage,footerData=footerData)