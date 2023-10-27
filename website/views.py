from flask import Flask, render_template, request, redirect, url_for, session
import pyrebase
from flask_session import Session
import functions.config as config
import functions.user as user



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
	return render_template('index.html')


# impliment cryptogrophy later
# sign up page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
     if(session['token'] == ""):
          if request.method == 'POST':
               user.forms(request.form)
               try:
                    user.create_user(auth, db)
                    return redirect(url_for('login'))
               except:
                    error = 'Invalid email or email already exists! Please also make sure password is atleast 6 characters long.'
                    return render_template('signup.html', msg=error)
               
          else:
               return render_template('signup.html', msg='')
     else:
          return "<h1>You are already logged in!</h1>"
          
     


# login page
@app.route('/login', methods=['GET','POST'])
def login():
     if request.method == 'POST':
          user.forms(request.form)
          try:
               user.login(auth)
               session['token'] = user.user_token['localId']
               return redirect(url_for('dashboard'))
          except:
               error = 'invalid email or password'
               return render_template('login.html', msg=error)
     else:
          return render_template('login.html', msg='')


# TODO: create logout page
@app.route('/logout')
def logout():
     session['token'] = ''
     user.logoff()
     return redirect(url_for('index'))


# TODO: create dashboard page 
@app.route('/dashboard')
def dashboard():
     token = session.get('token', 'session error')
     if token == '':
          return redirect(url_for('login'))
     else:
          user = db.child("user").get()
          data = {}
          for favorite in user.val()[token]['favorites']:
               data.update({
                    favorite:{
                         'href':favorite.replace(' ', '+'),
                         'caption':favorite
                    }
               })
          return render_template('dashboard.html', user_data=data)


# view list of recpies
@app.route('/recipe', methods=['GET'])
def recipe():
    recipe_links = user.recipe_to_links(db)
    return render_template('recipe.html', recipes=recipe_links)


# search page, need to fix and impliment error handling.
# (will fall on its face if it is not exact match, use python string magic or something idk)
# TODO: may need to rethink implimentation, this is not a good approach
@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        search_recipe = request.form['nm']
        search_recipe = search_recipe.replace(' ', '+')
        return redirect(f'/recipe/{search_recipe}')
    else:      
        return render_template('search.html')
    

# view recipe
@app.route('/recipe/<selection>', methods=['POST', 'GET'])
def viewRecipe(selection):
     favorite_flag = 'favorite'
     selection = selection.replace('+', ' ')

     data = db.child('Recipes').child(selection).get()
     token = session.get('token', 'session error')
     user = db.child("user").get()
     favorite_list = []

     for favorite in user.val()[token]['favorites']:
          if favorite == selection:
               favorite_flag = 'unfavorite'
          else:
               favorite_list.append(favorite)

     if request.method == 'POST':
          # check for token
          if token != '':
               if favorite_flag == 'favorite':
                    favorite_list.append(selection)
                    db.child('user').child(token).update({'favorites':favorite_list})
               else:
                    db.child('user').child(token).update({'favorites':favorite_list})

               return redirect(url_for('viewRecipe', selection=selection))
          else:
               return redirect(url_for('login'))
          
     else:
          return render_template('selection.html', 
                              dataInput=data.val(), recipeName=selection, fav=favorite_flag)


if __name__ == '__main__':
    app.run()