from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User 
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


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///restaurantmenuwithusers.db',connect_args={'check_same_thread':False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

       
 # Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))                                       #create randome numbers of 32chars for state of the login session
    login_session['state'] = state
    print("jatin - " + state)
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token


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
    return output
    
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
        print "Token's client ID does not match app's."
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
    print "done!"
    if getUserID(login_session['email']) == None:
        createUser(login_session)
    return output

#@app.route('/gdisconnect')
@app.route('/disconnect')
def disconnect():
    print(login_session['provider'] )
    if login_session['provider'] == 'facebook':
        facebook_id = login_session['facebook_id']
        # The access token must me included to successfully logout
        access_token = login_session['access_token']
        url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
        h = httplib2.Http()
        result = h.request(url, 'DELETE')[1]
        print(url)
        print(result)
        del login_session['access_token']
        del login_session['provider']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['facebook_id']
        #return "you have been logged out"
        flash('Successfully Logged out!!')
        return redirect(url_for('showRestaurants'))
        
    else:
        access_token = login_session.get('access_token')
        if access_token is None:
            print 'Access Token is None'
            response = make_response(json.dumps('Current user not connected.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        print 'In disconnect access token is %s', access_token
        print 'User name is: '
        print login_session['username']
        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]
        print(url)
        print 'result is '
        print result
        if result['status'] == '200':
            del login_session['access_token']
            del login_session['provider']
            del login_session['gplus_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            response = make_response(json.dumps('Successfully disconnected.'), 200)
            response.headers['Content-Type'] = 'application/json'  
            print response
            #return response
            flash('Successfully Logged out!!')
            return redirect(url_for('showRestaurants'))
        else:
            response = make_response(json.dumps('Failed to revoke token for given user.', 400))
            response.headers['Content-Type'] = 'application/json'
            return response

# JSON APIs to view Restaurant Information
@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(Menu_Item=Menu_Item.serialize)


@app.route('/restaurant/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])


# Show all restaurants
@app.route('/')
@app.route('/restaurant/')
def showRestaurants():
    if 'username' not in login_session:  
        #print("check1")
        restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
        return render_template('restaurants.html', restaurants=restaurants, currentUserName="none")        
    else:    
        #print(restaurant.name + " - " + str(restaurant.user_id))
        currentUserName = login_session['username']
        print(currentUserName)
        restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
        return render_template('restaurants.html', restaurants=restaurants, currentUserName=currentUserName)   
        
# Create a new restaurant


@app.route('/restaurant/new/', methods=['GET', 'POST'])
def newRestaurant():
    user = getUserInfo(getUserID(login_session['email']))
    print(user.id)
    print(user.email)
    print(user.picture)
    print(user.name)
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        #print(login_session)
        newRestaurant = Restaurant(name=request.form['name'], user_id=getUserID(login_session['email']))
        session.add(newRestaurant)
        flash('New Restaurant %s Successfully Created' % newRestaurant.name)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newRestaurant.html')

# Edit a restaurant


@app.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedRestaurant = session.query(
        Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        currentUser = getUserID(login_session['email'])
        if currentUser == editedRestaurant.user_id:
            if request.form['name']:
                editedRestaurant.name = request.form['name']
                flash('Restaurant Successfully Edited %s' % editedRestaurant.name)
                return redirect(url_for('showRestaurants'))
        else:
            flash('Restaurant CANNOT be Edited as you are not the owner of the restaurant%s' % editedRestaurant.name)
            return redirect(url_for('showRestaurants'))            
    else:
        currentUser = getUserID(login_session['email'])
        if currentUser != editedRestaurant.user_id:
            flash('You cannot edit this Restaurant because you are not the creator!!')
        return render_template('editRestaurant.html', restaurant=editedRestaurant, currentUser=currentUser)


# Delete a restaurant
@app.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurantToDelete = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        currentUser = getUserID(login_session['email'])
        if currentUser == restaurantToDelete.user_id:
            session.delete(restaurantToDelete)
            flash('%s Successfully Deleted' % restaurantToDelete.name)
            session.commit()
            return redirect(url_for('showRestaurants', restaurant_id=restaurant_id))
        else:
            flash('Restaurant CANNOT be Deleted as you are not the owner of the restaurant%s' % restaurantToDelete.name)
            return redirect(url_for('showRestaurants', restaurant_id=restaurant_id))   
    else:
        currentUser = getUserID(login_session['email'])
        if currentUser != restaurantToDelete.user_id:
            flash('You cannot DELETE this Restaurant because you are not the creator!!')
        return render_template('deleteRestaurant.html', restaurant=restaurantToDelete, currentUser=currentUser)

# Show a restaurant menu


@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
        
    if 'username' not in login_session:        
        print(restaurant.name + " - " + str(restaurant.user_id))
        return render_template('menu.html', items=items, restaurant=restaurant, currentUser="none")
    else:
        currentUser = getUserInfo(getUserID(login_session['email']))
        print(restaurant.name + " - " + str(restaurant.user_id) + str(currentUser.id))
        return render_template('menu.html', items=items, restaurant=restaurant, currentUser=currentUser)
    
    


# Create a new menu item
@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        newItem = MenuItem(name=request.form['name'], description=request.form[
                           'description'], price=request.form['price'], course=request.form['course'], restaurant_id=restaurant_id, user_id=restaurant.user_id)
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('newmenuitem.html', restaurant_id=restaurant_id)

# Edit a menu item


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        currentUser = getUserID(login_session['email'])
        if currentUser == editedItem.user_id:
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']
            if request.form['price']:
                editedItem.price = request.form['price']
            if request.form['course']:
                editedItem.course = request.form['course']
            session.add(editedItem)
            session.commit()
            flash('Menu Item Successfully Edited')
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))
        else:
            flash('Menu Item CANNOT be Edited as you are not the creator!!')
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))            
    else:
        currentUser = getUserID(login_session['email'])
        if currentUser != editedItem.user_id:
            flash('You cannot EDIT this Menu Item because you are not the creator!!')        
        return render_template('editmenuitem.html', restaurant_id=restaurant_id, menu_id=menu_id, item=editedItem, currentUser=currentUser)


# Delete a menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        currentUser = getUserID(login_session['email'])
        if currentUser == itemToDelete.user_id:
            session.delete(itemToDelete)
            session.commit()
            flash('Menu Item Successfully Deleted')
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))
        else:
            flash('Menu Item CANNOT be Deleted as you are not the creator!!')
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))   
    else:
        currentUser = getUserID(login_session['email'])
        if currentUser != itemToDelete.user_id:
            flash('You cannot DELETE this Menu Item because you are not the creator!!')       
        return render_template('deleteMenuItem.html', item=itemToDelete, currentUser=currentUser)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)