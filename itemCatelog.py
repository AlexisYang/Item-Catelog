from flask import Flask, request, render_template, redirect, url_for,\
     jsonify, flash
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item
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
app = Flask(__name__)


engine = create_engine('sqlite:///itemcatelog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = 'Enter google oauth client id here'


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    print 'state: ', state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    print 'reqest_state: ', request.args.get('state')
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
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
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
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given\
                                             user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catelog/JSON')
def catelogJSON():
    categories = session.query(Category).all()
    items_all = session.query(Item)
    json_list = []
    for c in categories:
        items = items_all.filter_by(category_id=c.id).all()
        json_list.append(dict(c.serialize, Item=[i.serialize for i in items]))
    return jsonify(Category=json_list)


@app.route('/')
@app.route('/catelog/')
def catelog():
    # print login_session['state']
    category_all = session.query(Category).all()
    latest_items = session.query(Item).order_by(desc(Item.time))\
                          .limit(10).all()
    # login = 'Logout' if IS_LOGIN else 'Login'
    print login_session.__dict__
    login = 'Logout' if 'logged_in' in login_session else 'Login'
    return render_template('catelog.html',
                           categories=category_all,
                           latest_items=latest_items,
                           login_stats=login)


@app.route('/catelog/<string:category_name>/items/')
def categoryItem(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    item_all = session.query(Item).filter_by(category_id=category.id).all()
    return render_template('item_list.html', category=category, items=item_all)


@app.route('/catelog/<string:category_name>/<string:item_name>/')
def itemDesc(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(category_id=category.id,
                                         name=item_name).one()
    return render_template('item.html', category_name=category_name, item=item)


@app.route('/catelog/new/', methods=['GET', 'POST'])
def itemAdd():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newName = request.form['name']
        categoryId = request.form['category']
        desc = request.form['description']
        itemNames = [i.name for i in session.query(Item).all()]
        if newName not in itemNames:
            newItem = Item(name=newName, description=desc,
                           category_id=categoryId, time=datetime.now())
            session.add(newItem)
            session.commit()
        category_all = session.query(Category).all()
        latest_items = session.query(Item).order_by(Item.time.desc())\
                              .limit(10).all()
        return render_template('catelog.html',
                               categories=category_all,
                               latest_items=latest_items)
    else:
        category_all = session.query(Category).all()
        return render_template('new_item.html', categories=category_all)


@app.route('/catelog/<string:item_name>/edit/', methods=['GET', 'POST'])
def itemEdit(item_name):
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(name=item_name).one()
    categories = session.query(Category).all()
    if request.method == 'POST':
        item.category_id = request.form['category']
        item.description = request.form['desc']
        session.commit()
        latest_items = session.query(Item).order_by(desc(Item.time)).limit(10)\
                              .all()
        return render_template('catelog.html',
                               categories=categories,
                               latest_items=latest_items)
    else:
        current_cat = session.query(Category).filter_by(id=item.category_id)\
                             .one().name
        return render_template('edit_item.html',
                               item=item,
                               categories=categories,
                               current_cat=current_cat)


@app.route('/catelog/<string:item_name>/delete/', methods=['GET', 'POST'])
def itemDelete(item_name):
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(name=item_name).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        categories = session.query(Category).all()
        latest_items = session.query(Item).order_by(desc(Item.time)).limit(10)\
                              .all()
        return render_template('catelog.html',
                               categories=categories,
                               latest_items=latest_items)
    else:
        current_cat = session.query(Category).filter_by(id=item.category_id)\
                             .one().name
        return render_template('delete_item.html',
                               item=item,
                               category_name=current_cat)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
