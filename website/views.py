from flask import Flask, render_template, request, redirect, flash, url_for, session
import pyrebase
from flask_session import Session
import functions.config as config
import functions.user as user
from functions.favorite import add_favorite, remove_favorite, is_favorited
from functions.meal_plan import is_planned, add_planned, remove_planned


# TODO: impliment cryptography if adding passwords

app = Flask(__name__)

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app) # user sessions stored server side for now

# connect app to firebase
firebase = pyrebase.initialize_app(config.firebaseConf)
# auth reference
auth = firebase.auth()
# database refernce
db = firebase.database()
# initialize user class
user = user.UserData()


# Defining the home page of our site
@app.route('/')  # this sets the route to this page d
def index():
     # handle new users with no token (avoiding key error)
     if session.get('token') is None:
          session['token'] = ''
     # passing empty token, do not want to check for login
     return render_template('index.html', tokenTest='')


# impliment cryptogrophy later
# sign up page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
     if(session['token'] == ''):
          if request.method == 'POST':
               user.forms(request.form)
               try:
                    user.create_user(auth, db)
                    return redirect(url_for('login'))
               except:
                    error = '*Invalid email or email already exists! Please also make sure password is atleast 6 characters long.'
                    return render_template('signup.html', msg=error)
               
          else:
               return render_template('signup.html', msg='')

     else:
          return render_template('index.html', tokentTest=session['token'])
          
     
# login page
@app.route('/login', methods=['GET','POST'])
def login():
     if(session['token'] == ""):
          if request.method == 'POST':
               user.forms(request.form)
               try:
                    user.login(auth)
                    session['token'] = user.user_token['localId']
                    return redirect(url_for('dashboard'))
               except:
                    error = '*invalid email or password'
                    return render_template('login.html', msg=error)
          else:
               return render_template('login.html', msg='')
     else:
          return render_template('index.html', tokenTest=session['token'])


# TODO: create logout page
@app.route('/logout')
def logout():
     session['token'] = ''
     session['alert'] = ''
     user.logoff()
     return redirect(url_for('index'))


# TODO: create dashboard page, impliment favorite feature here
@app.route('/dashboard')
def dashboard():
     token = session.get('token', 'session error')
     if token == '':
          return redirect(url_for('login'))
     else:
          fav_links = user.user_recipies_to_links(db, token, 'favorites')
          plan_links = user.user_recipies_to_links(db, token, 'meal_plan')

          return render_template('dashboard.html', fav_data=fav_links, plan_data=plan_links)


# view list of recpies
@app.route('/recipe', methods=['GET'])
def recipe():
    recipe_links = user.recipe_to_links(db)
    return render_template('recipe.html', recipes=recipe_links)


# view recipe
@app.route('/recipe/<selection>', methods=['POST', 'GET'])
def viewRecipe(selection):
     selection = selection.replace('+', ' ')
     check_box_fav = ''
     check_box_planned = '' # for Aiden
     # get recipies
     recipe_data = user.get_recipe_data(db, selection) 

     # get user data if exists
     if(session['token'] != ""):
          token = session.get('token', 'session error')
          user_data = user.get_user_data(db)
          # check favorited or not
          check_box_fav, favorites = is_favorited(user_data, token, selection)
          check_box_planned, planned = is_planned(user_data, token, selection)
     
     # user clicks submit button
     if request.method == 'POST':
          # check for token
          if session['token'] != '':
               # check if favorited
               if request.form.get('favorite'):
                    add_favorite(db, token, favorites, selection)
               else:
                    remove_favorite(db, token, favorites, selection)

               #  check if planned 
               if request.form.get('plan'):
                    add_planned(db, token, planned, selection)
               else:
                    remove_planned(db, token, planned, selection)
                    
               return redirect(url_for('viewRecipe', selection=selection))
          else:
               return redirect(url_for('login'))
          
     else:
          return render_template('selection.html', 
                              dataInput=recipe_data.val(), recipeName=selection, favorited=check_box_fav, planned=check_box_planned)



if __name__ == '__main__':
    app.run()
