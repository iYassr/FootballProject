from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Club, Player, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
# maintain the same connection per thread
from sqlalchemy.pool import SingletonThreadPool

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "FootballClubs"


# Connect to Database and create database session
engine = create_engine(
    'sqlite:///Clubs.db?check_same_thread=false', poolclass=SingletonThreadPool)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


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
        print("Token's client ID does not match app's.")
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

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
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
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
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

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.'))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Players Information
@app.route('/Club/<int:club_id>/player/JSON')
def ClubPlayerJSON(club_id):
    club = session.query(Club).filter_by(id=club_id).one()
    items = session.query(Player).filter_by(
        club_id=club_id).all()
    return jsonify(players=[i.serialize for i in items])


# JSON APIs to view player Information
@app.route('/Club/<int:club_id>/player/<int:player_id>/JSON')
def playerJSON(club_id, player_id):
    player = session.query(Player).filter_by(id=player_id).one()
    return jsonify(player=player.serialize)


# JSON APIs to view list all clubs
@app.route('/Club/JSON')
def ClubsJSON():
    clubs = session.query(Club).all()
    return jsonify(clubs=[r.serialize for r in clubs])


# Show all Clubs
@app.route('/')
@app.route('/Club/')
def showClubs():
    clubs = session.query(Club).all()
    if 'username' not in login_session:
        return render_template('Clubs.html', clubs=clubs)
    else:
        return render_template('Clubs.html', clubs=clubs)

# Create a new Club
@app.route('/Club/new/', methods=['GET', 'POST'])
def newClub():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newClub = Club(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newClub)
        flash('New Club %s Successfully Created' % newClub.name)
        session.commit()
        return redirect(url_for('showClubs'))
    else:
        return render_template('newClub.html')

# Edit a Club


@app.route('/Club/<int:club_id>/edit/', methods=['GET', 'POST'])
def editClub(club_id):
    editedClub = session.query(
        Club).filter_by(id=club_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedClub.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this Club. Please create your own Club in order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedClub.name = request.form['name']
            flash('Club Successfully Edited %s' % editedClub.name)
            return redirect(url_for('showClubs'))
    else:
        return render_template('editClub.html', club=editedClub)


# Delete a Club
@app.route('/Club/<int:club_id>/delete/', methods=['GET', 'POST'])
def deleteClub(club_id):
    clubToDelete = session.query(
        Club).filter_by(id=club_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if clubToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this Club. Please create your own Club in order to delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(clubToDelete)
        flash('%s Successfully Deleted' % clubToDelete.name)
        session.commit()
        return redirect(url_for('showClubs'))
    else:
        return render_template('deleteClub.html', club=clubToDelete)

# Show Club Players


@app.route('/Club/<int:club_id>/')
@app.route('/Club/<int:club_id>/players/')
def showClub(club_id):
    club = session.query(Club).filter_by(id=club_id).one()
    creator = getUserInfo(club.user_id)
    players = session.query(Player).filter_by(
        club_id=club_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicplayers.html', players=players, club=club, creator=creator)
    else:
        return render_template('players.html', players=players, club=club, creator=creator)


# Create a new player
@app.route('/Club/<int:club_id>/player/new/', methods=['GET', 'POST'])
def newPlayer(club_id):
    if 'username' not in login_session:
        return redirect('/login')
    club = session.query(Club).filter_by(id=club_id).one()
    if login_session['user_id'] != club.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add player items to this Club. Please create your own Club in order to add items.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        newPlayer = Player(name=request.form['name'], position=request.form['position'], market_value=request.form[
            'market_value'], age=request.form['age'], nationality=request.form['nationality'], club_id=club_id, user_id=club.user_id)
        session.add(newPlayer)
        session.commit()
        flash('New Player %s Item Successfully Created' % (newPlayer.name))
        return redirect(url_for('showClub', club_id=club_id))
    else:
        return render_template('newPlayer.html', club_id=club_id)

# Edit Player
@app.route('/Club/<int:club_id>/player/<int:player_id>/edit', methods=['GET', 'POST'])
def editPlayer(club_id, player_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedPlayer = session.query(Player).filter_by(id=player_id).one()
    club = session.query(Club).filter_by(id=club_id).one()
    if login_session['user_id'] != club.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit player to this Club. Please create your own Club in order to edit items.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedPlayer.name = request.form['name']
        if request.form['position']:
            editedPlayer.position = request.form['position']
        if request.form['market_value']:
            editedPlayer.market_value = request.form['market_value']
        if request.form['age']:
            editedPlayer.age = request.form['age']
        session.add(editedPlayer)
        session.commit()
        flash('Player Item Successfully Edited')
        return redirect(url_for('showClub', club_id=club_id))
    else:
        return render_template('editPlayer.html', club_id=club_id, player_id=player_id, player=editedPlayer)


# Delete a player
@app.route('/Club/<int:club_id>/player/<int:player_id>/delete', methods=['GET', 'POST'])
def deletePlayer(club_id, player_id):
    if 'username' not in login_session:
        return redirect('/login')
    club = session.query(Club).filter_by(id=club_id).one()
    playerToDelete = session.query(Player).filter_by(id=player_id).one()
    if login_session['user_id'] != club.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete player to this Club. Please create your own Club in order to delete items.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(playerToDelete)
        session.commit()
        flash('Player Successfully Deleted')
        return redirect(url_for('showClub', club_id=club_id))
    else:
        return render_template('deletePlayer.html', player=playerToDelete)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showClubs'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showClubs'))


if __name__ == '__main__':
    app.secret_key = 'donottellanyone'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
