from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, exc
from sqlalchemy.orm import sessionmaker, joinedload
from database_setup import Base, Categories, Items, User 
from flask import session as login_session
import random
import string

# IMPORTS FOR THIS STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
#app.config['JSON_SORT_KEYS'] = False #uncomment it if you want to see unsorted JSON endpoint data. 


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///catalogapp.db',connect_args={'check_same_thread':False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# START OF VARIOUS HELPER FUNCTIONS
# creates user from google and FB logins 
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id
    
# creates user local form provided     
def createLocalUser(email,fname,lname,password):
    fullname = fname + " " + lname 
    newUser = User(name=fullname, email=email, picture="", password=password)
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=email).one()
    return user.name

# authenticateLocalUser
def authenticateLocalUser(email,password):
    check = 0
    user = session.query(User).filter_by(email=email).one()
    if(user.password == password):
        check = 1    
    return check
    
def getLocalUser(email):
    #user = session.query(User).filter_by(email=email).one() commented out as no need for password to be part of the object
    user = session.query(User).filter_by(email=email).with_entities(User.id,User.name,User.email,User.picture).one()
    return user
    
# User Helper Functions
def getCategories():
    #items = session.query(Categories).all()
    items = session.query(Categories).order_by(asc(Categories.name))
    return items
    
# get a partucular category using name
def getCategoryID(name):
    item = session.query(Categories).filter_by(name=name).one()
    return item.id
    
# get description of the item given name of catagory and title of the item    
def getItemFromCategoryNameItemTitle(name,title):
    check = 0
    try:
        item = (session.query(Items)
            .filter(Items.category_id == Categories.id)
            .filter(Items.title == title)
            .filter(Categories.name == name)
            .one())
        return item
    except exc.SQLAlchemyError:
           return check
    
#check if category existing given name
def existCategory(category_name):
    check = 0
    items = getCategories()
    for item in items:
        if(item.name == category_name):
            check = 1
    return check
# get items given category id
def getAllItems():
    items = session.query(Items).order_by(asc(Items.title))
    return items
    
def getLastTenItemsAdded():
    items = session.query(Items).order_by(Items.id.desc()).limit(10)
    return items

def getCategoryItems(category_id):
    items = session.query(Items).filter_by(category_id=category_id).all()
    return items
    
def getItemsCount(category_id):
    count = session.query(Items).filter_by(category_id=category_id).count()
    return count

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def itemExistCheck(title,name):
    check = 0
    try:
        session.query(Items).filter(Items.category_id == Categories.id).filter(Items.title == title).filter(Categories.name == name).one()
        check = 1
    except exc.SQLAlchemyError:
        pass
    return check
    
def itemOwnerCheck(title,name,user_id):
    check = 0
    try:
        session.query(Items).filter(Items.category_id == Categories.id).filter(Items.title == title).filter(Categories.name == name).filter(Items.user_id == user_id).one()
        check = 1
    except exc.SQLAlchemyError:
        pass
    return check
    
def createItem(title,description,user_id,category_name):
    check = 0
    #check item and category combination if exist
    if not itemExistCheck(title,category_name):
        #creating category
        if not existCategory(category_name):
            category = Categories(name=category_name,user_id=user_id)
            session.add(category)
            session.commit()
            category_id = category.id
        else:
            category_id = getCategoryID(category_name)
        
        #creating item
        try:
            item = Items(title=title,description=description,category_id=category_id,user_id=user_id)
            session.add(item)
            session.commit()  
            check = 1
        except exc.SQLAlchemyError:
            pass            
    return check

def editItem(title,description,user_id,category_name,current_category_name):
    check = 0
    # YOU MUST GET THE ITEM FIRST IN ORDER TO EDIT OTHERWISE IT WILL NOT WORK
    editItem = getItemFromCategoryNameItemTitle(current_category_name,title)
    #check if category  exist
    if not existCategory(category_name):
        category = Categories(name=category_name,user_id=user_id)
        session.add(category)
        session.commit()
        category_id = category.id
    else:
        category_id = getCategoryID(category_name)        
    #updating item
    try:
        # AT THE TIME OF EXIT LEAVE THE FOREIGH KEY AND PRIMARY KEY ALONE AND ONLY FOCUS ON THE ACTUAL DATA THAT YOU WANT TO EXID OTHER WISE YOU WILL GET sqlite3.IntegrityError WHEN YOU TRY TO EDIT WITH THOSE KEYS
        # ALSO DO NOT USE THE ITEM CLASS THAT WILL CREATE NEW ITEM NOT UPDATE EXISTING
        #item = Items(id=item.id,title=title,description=description,category_id=category_id,user_id=user_id) #1st failed attempt
        #item = Items(title=title,description=description,category_id=category_id) #2nd failed attempt
        editItem.title = title
        editItem.description = description
        editItem.category_id = category_id
        session.add(editItem)
        session.commit()
        check = 1
    except exc.SQLAlchemyError:
        pass    
    return check    
  
def deleteItem(title,category_name):
    check = 0
    # YOU MUST GET THE ITEM FIRST IN ORDER TO DELETE OTHERWISE IT WILL NOT WORK
    deleteItem = getItemFromCategoryNameItemTitle(category_name,title)
    #updating item
    try:
        session.delete(deleteItem)
        session.commit()
        check = 1
    except exc.SQLAlchemyError:
        pass    
    return check  
# END OF HELPER FUNCTIONS
   
# Create anti-forgery state token
@app.route('/login', methods=['GET','POST'])
def showLogin():
    if request.method == 'POST':
        return localUserLogin(request.form['email'],request.form['pwd'])        
    else:    
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))                                       #create randome numbers of 32chars for state of the login session
        login_session['state'] = state
        # return "The current session state is %s" % login_session['state']
        return render_template('login.html', STATE=state)

#Local user login        
@app.route('/localuserlogin', methods=['GET','POST'])
def localUserLogin(email,password):
    if(authenticateLocalUser(email,password)):
        user = getLocalUser(email)
        #print(user)
        login_session['username'] = user.name
        login_session['picture'] = user.picture
        login_session['email'] = user.email
        login_session['provider'] = 'local'
        flash("you are now logged in as %s" % login_session['username'])
        currentUserName = login_session['username']
        #return render_template('catalog.html', categories=categories, items=items, currentUserName=currentUserName,showLatest="true")  
        return redirect(url_for('showCategoriesLatestItems'))         
    else:
        flash("incorrect username and/or password, please try again")
        return redirect(url_for('showLogin'))
        
#Facebook login
@app.route('/fbconnect', methods=['POST'])
def fbconnect():

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    #print "access token received %s " % access_token


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token

    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    if getUserID(login_session['email']) == None:
        createUser(login_session)
    return output

#Google login    
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        #print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['email']   ## this might not work if you dont have the g+ account so changed from 'name' to 'email'
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    #print(login_session)
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'


    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    #print "done!"
    if getUserID(login_session['email']) == None:
        createUser(login_session)
    return output

#Logging out user
@app.route('/disconnect')
def disconnect():
    #print("test - " + login_session['provider'] )
    if login_session['provider'] == 'facebook':
        facebook_id = login_session['facebook_id']
        # The access token must me included to successfully logout
        access_token = login_session['access_token']
        url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
        h = httplib2.Http()
        result = h.request(url, 'DELETE')[1]
        #print(url)
        #print(result)
        del login_session['access_token']
        del login_session['provider']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['facebook_id']
        #return "you have been logged out"
        flash('Successfully Logged out!!')
        return redirect(url_for('showCategoriesLatestItems'))
        
    elif login_session['provider'] == 'local':
        del login_session['provider']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        #return "you have been logged out"
        flash('Successfully Logged out!!')
        return redirect(url_for('showCategoriesLatestItems'))
        
    else:
        access_token = login_session.get('access_token')
        if access_token is None:
            print 'Access Token is None'
            response = make_response(json.dumps('Current user not connected.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        #print 'In disconnect access token is %s', access_token
        #print 'User name is: '
        #print login_session['username']
        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]
        if result['status'] == '200':
            del login_session['access_token']
            del login_session['provider']
            del login_session['gplus_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            response = make_response(json.dumps('Successfully disconnected.'), 200)
            response.headers['Content-Type'] = 'application/json'  
            #print response
            #return response
            flash('Successfully Logged out!!')
            return redirect(url_for('showCategoriesLatestItems'))
        else:
            # force clear login_session
            del login_session['access_token']
            del login_session['provider']
            del login_session['gplus_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            #del login_session['state']
            flash('Successfully Logged out!!')
            #response = make_response(json.dumps('Failed to revoke token for given user.', 400))
            #response.headers['Content-Type'] = 'application/json'
            #eturn response
            return redirect(url_for('showCategoriesLatestItems'))

# Show all catalog items
@app.route('/')
@app.route('/catalog')
def showCategoriesLatestItems():
    categories = getCategories()
    #items = getAllItems()
    items = getLastTenItemsAdded() #gets last 10 items added
    items = sorted(items, key=lambda items: items.title) #this sorts in asceding order by title
    #print(login_session)    
    if 'username' not in login_session:  
        #print("check1")
        return render_template('catalog.html', categories=categories, items=items, currentUserName="none",showLatest="true")        
    else:    
        #print(restaurant.name + " - " + str(restaurant.user_id))
        currentUserName = getLocalUser(login_session['email'])
        #print(currentUserName)
        return render_template('catalog.html', categories=categories, items=items, currentUserName=currentUserName,showLatest="true")   

@app.route('/catalog/<string:name>/items')   
def showCategoriesSelectedItems(name):  
    categories = getCategories()
    category_id = getCategoryID(name)
    itemcount = getItemsCount(category_id)
    items = getCategoryItems(category_id)
    #print(itemcount)
    if 'username' not in login_session:  
        #print("check1")
        return render_template('catalog.html', categories=categories, items=items, count=itemcount, name=name, currentUserName="none",showCategoryItem="true")        
    else:    
        #print(restaurant.name + " - " + str(restaurant.user_id))
        currentUserName = getLocalUser(login_session['email'])
        #print(currentUserName)
        return render_template('catalog.html', categories=categories, items=items, count=itemcount,name=name, currentUserName=currentUserName,showCategoryItem="true")   

# Item Description
@app.route('/catalog/<string:name>/<string:title>')     
def showItemDescription(name,title):
    # now we have to seclect the description where which matches title from item and name from catagories
    categories = getCategories()
    item = getItemFromCategoryNameItemTitle(name,title)
    if(item):
        if 'username' not in login_session:  
            #print("check1")
            return render_template('catalog.html', categories=categories, item=item, currentUserName="none",name=name,showDescription="true")        
        else:    
            #print(restaurant.name + " - " + str(restaurant.user_id))
            currentUserName = getLocalUser(login_session['email'])
            #print("showItemDescription - ",currentUserName)
            return render_template('catalog.html', categories=categories, item=item, currentUserName=currentUserName,name=name,showDescription="true")  
    else:
        print("showItemDescription")
        flash('Item does not exist')
        return redirect(url_for('showCategoriesLatestItems'))


# for creating local users        
@app.route('/userinfo',methods=['GET', 'POST'])
def getUserInfo():
    categories = getCategories()
    items = getAllItems()
    #print(login_session)    
    if request.method == 'POST':
        if 'username' not in login_session:
            user_id = getUserID(request.form['email'])
            if not user_id:
                newUser = createLocalUser(email=request.form['email'], fname=request.form['fname'], lname=request.form['lname'], password=request.form['pwd'])
                flash('New User %s Successfully Created, click on Login to login as new user' % (newUser))
                #return redirect(url_for('showCategoriesLatestItems'))   # doing double work so not using redirect...
                return render_template('catalog.html', categories=categories, items=items, currentUserName="none",showLatest="true") 
            else:
                flash('Email  %s already exist, Please select different Email address' % (request.form['email']))
                return render_template('catalog.html', categories=categories, items=items, currentUserName="none",newUser='true')
        else:
            currentUserName = getLocalUser(login_session['email'])
            flash('User already logged in as   %s' % (currentUserName))
            return render_template(url_for('catalog.html', categories=categories, items=items, currentUserName=currentUserName,showLatest="true"))
    else:
        if 'username' not in login_session: 
            return render_template('catalog.html', categories=categories, items=items, currentUserName="none",newUser='true')        
        else:    
            currentUserName = getLocalUser(login_session['email']) # currentUserName = login_session['username']
            flash('User already logged in as   %s' % (currentUserName)) 
            return render_template('catalog.html', categories=categories, items=items, currentUserName=currentUserName,showLatest="true")

# for creating new item   
@app.route('/newitem',methods=['GET', 'POST'])
def createNewItem():
    #print("createNewItem - ",user_id)
    #print(user.email)
    #print(user.picture)
    #print(user.name)
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        user_id = getUserID(login_session['email'])
        #print(login_session)
        newItem = createItem(request.form['title'],request.form['desc'],user_id,request.form['name'])
        if(newItem):
            flash('New Item %s Successfully Created' % request.form['title'])
            return redirect(url_for('showCategoriesLatestItems'))
        else: 
            categories = getCategories()
            items = getAllItems()
            currentUserName = getLocalUser(login_session['email'])
            flash('New Item %s already exist (may be create by someone else) ' % request.form['title'])
            return render_template('catalog.html', categories=categories, items=items, currentUserName=currentUserName,newItem="true")
    else:
        user_id = getUserID(login_session['email'])
        categories = getCategories()
        items = getAllItems()
        currentUserName = getLocalUser(login_session['email'])
        return render_template('catalog.html', categories=categories, items=items, currentUserName=currentUserName,newItem="true")
        
#http://localhost:8000/catalog/Snowboard/edit
@app.route('/catalog/<string:name>/<string:title>/edit',methods=['GET', 'POST'])
def editExistingItem(name,title):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        user_id = getUserID(login_session['email'])
        #print("editItem - ",user_id)
        #print(login_session)
        if(itemExistCheck(title,name)):
           # user_id = getUserID(login_session['email'])
            if(itemOwnerCheck(title,name,user_id)):
                updatedItem = editItem(request.form['title'],request.form['desc'],user_id,request.form['name'],name)
                if(updatedItem):
                    flash('Item Updated Successfully!!')
                    return redirect(url_for('showCategoriesLatestItems'))
                else:
                    flash('Unable to edit the item %s' % request.form['title'])
                    return redirect(url_for('showCategoriesLatestItems'))       
            else:
                flash('Item %s is not owned by your id so you cannot edit this item' % request.form['title'])
                return redirect(url_for('showCategoriesLatestItems'))      
        else:
            flash('Item %s does not exist' % request.form['title'])
            return redirect(url_for('showCategoriesLatestItems'))
    else:
        user_id = getUserID(login_session['email'])
        #print("editItem - ",user_id)
        if(itemExistCheck(title,name)):
            categories = getCategories()
            item = getItemFromCategoryNameItemTitle(name,title)
            currentUserName = getLocalUser(login_session['email'])
            return render_template('catalog.html', categories=categories, item=item, currentUserName=currentUserName,name=name,title=title,editItem="true")
        else:
            flash('Item %s does not exist that you want to edit' % request.form['title'])
            return redirect(url_for('showCategoriesLatestItems'))

#http://localhost:8000/catalog/Snowboard/delete            
@app.route('/catalog/<string:name>/<string:title>/delete',methods=['GET', 'POST'])
def deleteExistingItem(name,title):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        user_id = getUserID(login_session['email'])
        print("deleteItem - ",user_id)
        #print(login_session)
        if(itemExistCheck(title,name)):
           # user_id = getUserID(login_session['email'])
            if(itemOwnerCheck(title,name,user_id)):
                updatedItem = deleteItem(title,name)
                if(updatedItem):
                    flash('Item delete Successfully!!')
                    return redirect(url_for('showCategoriesLatestItems'))
                else:
                    flash('Unable to delete the item %s' % title)
                    return redirect(url_for('showCategoriesLatestItems'))       
            else:
                flash('Item %s is not owned by your id so you cannot delete this item' % title)
                return redirect(url_for('showCategoriesLatestItems'))      
        else:
            flash('Item %s does not exist' % title)
            return redirect(url_for('showCategoriesLatestItems'))
    else:
        user_id = getUserID(login_session['email'])
        #print("deleteItem - ",user_id)
        if(itemExistCheck(title,name)):
            categories = getCategories()
            item = getItemFromCategoryNameItemTitle(name,title)
            currentUserName = getLocalUser(login_session['email'])
            return render_template('catalog.html', categories=categories, item=item, currentUserName=currentUserName,name=name,title=title,deleteItem="true")
        else:
            flash('Item %s does not exist that you want to delete' % title)
            return redirect(url_for('showCategoriesLatestItems'))

            
#JSON Endpoint
@app.route('/catalog.json')
@app.route('/catalog/JSON')
def catalogJSON():
    # this one got some help from stackoverflow.com answers
    categories = session.query(Categories).options(joinedload(Categories.items)).all()
    return jsonify(Catalog=[dict(c.serialize, items=[i.serialize
                                                     for i in c.items])
                         for c in categories])
                         

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)