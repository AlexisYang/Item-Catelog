from flask import Flask, request, render_template, redirect, url_for,\
     jsonify, flash
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from database_setup import Base, Category, Item, User
from datetime import datetime
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import make_response
import random
import string
import httplib2
import json
import requests
import secret_key
app = Flask(__name__)
app.debug = True
secret_key.install_secret_key(app)

engine = create_engine('postgresql://catelog:catelog@localhost/catelog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = '1050364021346-l1r8r3j7jnis2i8e6oht3drlpk9q4a4t.apps.'\
            + 'googleusercontent.com'


@app.route('/login')
def showLogin():
    """
    Returns:
        string: login page
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Returns:
        flask.wrappers.Response: include following cases
            1. Invalid state parameter
            2. Failed to upgrade the authorization code
            3. There is an error in the access token info
            4. Token's user ID doesn't match given user ID
            5. Token's client ID does not match app's
            6. Current user is already connected
        String: when user is successfully logged in
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/html/Item-Catelog/client_secrets.json', scope='')
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
    result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))
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
        print('Token\'s client ID does not match app\'s.')
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already \
                                 connected.'), 200)
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

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['logged_in'] = True

    if not getUserID(data['email']):
        createUser(login_session)

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; \
                           height: 300px;\
                           border-radius: 150px;\
                           -webkit-border-radius: 150px;\
                           -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print('done!')
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """
    Returns:
        String: main page
    """
    access_token = login_session.get('access_token')
    if access_token is None:
        # response = make_response(json.dumps('Current user not connected.'),
        #                          401)
        # response.headers['Content-Type'] = 'application/json'
        # return response
        flash('Current user not connected.')
        return redirect('/catelog/')
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['logged_in']
        # response = make_response(json.dumps('Successfully disconnected.'),
        #                          200)
        # response.headers['Content-Type'] = 'application/json'
        # return response
        flash('Successfully disconnected.')
        return redirect('/catelog/')
    else:
        # response = make_response(json.dumps('Failed to revoke token for\
        #                                      given user.', 400))
        # response.headers['Content-Type'] = 'application/json'
        # return response
        flash('Failed to revoke token for given user.')
        return redirect('/catelog/')


@app.route('/catelog/JSON')
def catelogJSON():
    """
    Returns:
        flask.wrappers.Response: json field of all categories
                                 with relative items
    """
    categories = session.query(Category).all()
    items_all = session.query(Item)
    json_list = []
    for c in categories:
        items = items_all.filter_by(category_id=c.id).all()
        json_list.append(dict(c.serialize, Item=[i.serialize for i in items]))
    return jsonify(Category=json_list)


@app.route('/catelog/JSON/<int:category_id>/<int:item_id>/')
def itemJSON(category_id, item_id):
    """
    Args:
        category_id: (Integer) category id
        item_id: (Integer) item id
    Returns:
        flask.wrappers.Response: json field of specific item
    """
    item = session.query(Item).filter_by(id=item_id).first()
    return jsonify(Item=item.serialize)


@app.route('/')
@app.route('/catelog/')
def catelog():
    """
    Returns:
        flask.wrappers.Response: catelog page
    """
    user_name = ''
    category_all = session.query(Category).all()
    latest_items = session.query(Item).order_by(desc(Item.time))\
                          .limit(10).all()
    if 'logged_in' in login_session:
        user_name = login_session['username']
    return render_template('catelog.html',
                           categories=category_all,
                           latest_items=latest_items,
                           user_name=user_name)


@app.route('/catelog/<string:category_name>/items/')
def categoryItem(category_name):
    """
    Args:
        category_name: (String) category name
    Returns:
        flask.wrappers.Response: category page
    """
    category = session.query(Category).filter_by(name=category_name).one()
    item_all = session.query(Item).filter_by(category_id=category.id).all()
    return render_template('item_list.html', category=category, items=item_all)


@app.route('/catelog/<string:category_name>/<string:item_name>/')
def itemDesc(category_name, item_name):
    """
    Args:
        category_name: (String) category name
        item_name: (String) item name
    Returns:
        flask.wrappers.Response: item page
    """
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(category_id=category.id,
                                         name=item_name).one()
    user_name = getUserName(item.user_id)
    return render_template('item.html', category_name=category_name, item=item,
                           user_name=user_name)


@app.route('/catelog/new/', methods=['GET', 'POST'])
def itemAdd():
    """
    Returns:
        flask.wrappers.Response: login page if user is not logged in,
                                 else return new item page
    """
    if 'username' not in login_session:
        return redirect('/login')
    userId = getUserID(login_session['email'])
    if request.method == 'POST':
        newName = request.form['name']
        categoryId = request.form['category']
        desc = request.form['description']
        itemNames = [i.name for i in session.query(Item).all()]
        if newName not in itemNames:
            newItem = Item(name=newName, description=desc,
                           category_id=categoryId, time=datetime.now(),
                           user_id=userId)
            session.add(newItem)
            session.commit()
        return redirect('/catelog/')
    else:
        category_all = session.query(Category).all()
        return render_template('new_item.html', categories=category_all)


@app.route('/catelog/<string:item_name>/edit/', methods=['GET', 'POST'])
def itemEdit(item_name):
    """
    Args:
        item_name: (String) item name
    Returns:
        flask.wrappers.Response: item page if user is not permitted to edit,
                                 else return edit page
    """
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(name=item_name).one()
    category = session.query(Category).filter_by(id=item.category_id).one()
    username = getUserName(item.user_id)
    if not login_session['username'] == username:
        flash('You don\'t have permission to modify this item')
        return itemDesc(category.name, item.name)
    categories = session.query(Category).all()
    if request.method == 'POST':
        item.category_id = request.form['category']
        item.description = request.form['desc']
        session.commit()
        return redirect('/catelog/')
    else:
        return render_template('edit_item.html',
                               item=item,
                               categories=categories,
                               current_cat=category.name)


@app.route('/catelog/<string:item_name>/delete/', methods=['GET', 'POST'])
def itemDelete(item_name):
    """
    Args:
        item_name: (String) item name
    Returns:
        flask.wrappers.Response: item page if user is not permitted to delete,
                                 else return edit page
    """
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(name=item_name).one()
    category = session.query(Category).filter_by(id=item.category_id).one()
    username = getUserName(item.user_id)
    if not login_session['username'] == username:
        flash('You don\'t have permission to modify this item')
        return itemDesc(category.name, item.name)
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        categories = session.query(Category).all()
        return redirect('/catelog')
    else:
        return render_template('delete_item.html',
                               item=item,
                               category_name=category.name)


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except NoResultFound:
        return None


def getUserName(user_id):
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user.name
    except NoResultFound:
        return None


# print('apppppppppppppp')
# app.debug = True
# app.run()
if __name__ == '__main__':
    # app.secret_key = 'super_secret_key'
    app.run()
    # app.run(host='0.0.0.0', port=5000)
