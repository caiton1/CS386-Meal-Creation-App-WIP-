import sys
sys.path.append('../functions')
import allergy
import config
import user
import pyrebase


# connect app to firebase
firebase = pyrebase.initialize_app(config.firebaseConf)
# auth reference
auth = firebase.auth()
# database reference
db = firebase.database()
# initialize user class
user = user.UserData()

def test_get_recipe_data():
    recipes_data = user.get_recipes(db)
    recipes = []

    for recipe in recipes_data.each():
        # extracting data from database
        recipe_data = recipe.val()
        recipe_name = recipe.key()
        ingredients = list(recipe_data['Ingredients'])  # don't care about values
        description = recipe_data['Description']

        # append recipe details to list
        recipes.append({
            'Name': recipe_name,
            'Description': description,
            'Ingredients': ingredients,
        })

    assert allergy.get_recipe_data(user.get_recipes(db)) == recipes


def test_input_to_allergies():
   test_input = 'salt, bread, tomatoes, tears of the dammed'

   assert allergy.input_to_allergies(test_input) == ['salt', 'bread', 'tomatoes', 'tears of the dammed']


def test_filter__by_allergies():
    # if there are no allergies, return all the recipes
    allergies = ['salt']
    recipes = allergy.get_recipe_data(user.get_recipes(db))
    # create an empty list for the recipes without the allegies
    filtered_recipes = []
    # iterate through the recipes
    for recipe in recipes:
        # allergy flag for the current recipe
        has_allergy = False

        # iterate through the allergies list 
        for current in allergies:
            description = [desc.lower() for desc in recipe.get("Description")]
            #check if the current allergy is the the description or ingredients
            if current.lower() in description:
                # set the allergy flag to True
                has_allergy = True
                break
                

            ingredients = [ingredient.lower() for ingredient in recipe.get("Ingredients")]
            if current in ingredients:
                has_allergy = True
                break
        
        # If the current recipe doesn't have any allergies
        if not has_allergy:
            # Add recipe to the filtered list
            filtered_recipes.append(recipe)
    assert filtered_recipes == allergy.filter_by_allergies(recipes, allergies)


