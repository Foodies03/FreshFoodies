# from flask import Flask, session, redirect
from config import Configuration
from datetime import datetime, timezone
import os
import json
from pymongo.collection import Collection, ReturnDocument

import flask
from flask import Flask, request, jsonify, render_template, redirect
from flask_pymongo import PyMongo
from uuid import UUID, uuid4

from pymongo import MongoClient

# from bson import ObjectId

from pymongo.errors import DuplicateKeyError
from .objectid import PydanticObjectId

import certifi

# TODO: Add "expires in ... days"

# Set up flask app
app = Flask(__name__)
app.config.from_object(Configuration)
app.secret_key = os.urandom(24)  # Secret key for client authentication
app.url_map.strict_slashes = False

mongo_client = MongoClient(app.config['MONGO_URI'], uuidRepresentation='standard')
pymongo = PyMongo(app, tlsCAFile=certifi.where())

# blueprint for non-authentication parts of the app
from .food import food as food_blueprint
app.register_blueprint(food_blueprint)

from .receipt import receipt as receipt_blueprint
app.register_blueprint(receipt_blueprint)

from .models import Fridge, Food, User, Entry

"""
Test Account and Fridge
"""
# USER_ID = PydanticObjectId('63e374f9f538bd23252a2fd1')
# FRIDGE_ID = PydanticObjectId('63e37436f538bd23252a2fcf')

USER_ID = PydanticObjectId('663ace18ffd58bb442157938')
FRIDGE_ID = PydanticObjectId('663acdc9ffd58bb442157934')

# Get a reference to the fridge collection
fridges: Collection = pymongo.db.fridges
users: Collection = pymongo.db.users

recipes_collection: Collection = pymongo.db.recipes

@app.errorhandler(404)
def resource_not_found(e):
    """
    An error-handler to ensure that 404 errors are returned as JSON.
    """
    return jsonify(error=str(e)), 404


@app.errorhandler(DuplicateKeyError)
def resource_not_found(e):
    """
    An error-handler to ensure that MongoDB duplicate key errors are returned as JSON.
    """
    return jsonify(error=f"Duplicate key error."), 400

@app.route("/")
def index():
    greeting="Welcome to the LookingGlass API!"
    return render_template('index.html', message=greeting)

"""
Create new user

{
    "name": "",
    "email": "",
}

"""
@app.route("/api/signup", methods=["POST"])
def signup():
    message = ''
    if request.method == "POST":
        request_json = request.get_json()

        user = request_json["name"]
        email = request_json["email"]

        user_found = users.find_one({"name": user})
        email_found = users.find_one({"email": email})
        if user_found:
            message = 'There already is a user by that name'
            return render_template('index.html', message=message)
        if email_found:
            message = 'This email already exists in database'
            return render_template('index.html', message=message)
        else:
            user_input = {'name': user, 'email': email, 'fridge_ids': [], 'entries': []}
            user: User = User(**user_input)
            users.insert_one(user.to_bson())

            user_data: User = get_user_mongodb(email)
            return user_data.to_json()
    return render_template('index.html')


"""
GET
EXPECTS:
{
    "email":
}
"""
@app.route("/api/login", methods=["POST"])
def login():
    print("login request")
    request_json = request.get_json()
    email = request_json["email"]
    user: User = get_user_mongodb(email)
    print(email)
    if user:
        return jsonify({"email": email}), 200
    else:
        return jsonify({"error": "User not found"}), 404

# Route for logged in user
@app.route('/api/me', methods=["POST", "GET"])
def me():
    request_json = request.get_json()
    email = request_json["email"]
    user: User = get_user_mongodb(email)
    if user:
        return user.to_json()
    else:
        flask.abort(404, "User not found")

@app.route('/api/user/entries', methods=['POST'])
def get_entry_data():
    request_json = request.get_json()
    email = request_json['email']
    user: User = get_user_mongodb(email)
    if user:
        time_frame = request_json['time_frame']
        end_time = datetime.now(timezone.utc).replace(tzinfo=None)
        begin_time = datetime.fromisoformat(time_frame.rstrip("Z"))
        print(end_time)
        print(begin_time)
        raw_entries = users.find_one(
            {'email' : email}
        )['entries']
        if raw_entries:
            filtered_entries = [entry for entry in raw_entries if begin_time <= datetime.fromisoformat(entry['creation_time'].rstrip("Z")) <= end_time]
        else:
            print('could not find user')
        print(filtered_entries)
        return filtered_entries
    else:
        flask.abort(404, "User not found")

@app.route('/api/user/add_entry', methods=['POST'])
def add_entry():
    request_json = request.get_json()
    email = request_json['email']
    user: User = get_user_mongodb(email)

    if user:
        entry_details = request_json['entry_details']
        print('entry details:')
        print(entry_details['id'])
        new_entry_raw = {
            'food_name': entry_details["food_name"],
            'category': entry_details["category"],
            'entry_type': entry_details["entry_type"],
            'amount': entry_details['amount'],
            'cost_per_unit': entry_details['cost_per_unit'],
            'creation_time': entry_details['creation_time']
        }
        new_entry: Entry = Entry(**new_entry_raw).to_bson()
        added_entry = users.find_one_and_update(
            {'email': email},
            {'$push': {'entries': new_entry}},
            return_document=ReturnDocument.AFTER
        )

        if added_entry:
            print("successfully added entry")
            print(new_entry)
            print('food_id: ')
            id_to_remove = UUID(entry_details['id'])
            test_result = fridges.find_one(
                {'_id' : PydanticObjectId(entry_details['fridge_id'])},
            )
            print(test_result)
            result = fridges.find_one_and_update(
                {'_id' : PydanticObjectId(entry_details['fridge_id'])},
                {'$pull': {'foods': {'id': id_to_remove}}},
                return_document=ReturnDocument.AFTER
            )
            print('pull result')
            print(result)
        else:
            print("failed to add entry")

        return new_entry
    else:
        flask.abort(404, "user not found")

# Create new empty fridge
"""
POST
EXPECTS:
{
    "email": "email",
    "slug": "name"
}

RETURNS:
{
    "_id":"",
    "foods":[...],
    "slug":"",
    "users":[...]
}
"""
@app.route("/api/fridge", methods=["POST"])
def new_fridge():
    raw_fridge = request.get_json()
    fridge: Fridge = Fridge(**raw_fridge)
    fridge.foods = []
    email = raw_fridge["email"]
    fridge.slug = raw_fridge["slug"]
    fridge.users = [email]
    insert_result = fridges.insert_one(fridge.to_bson())
    fridge.id = PydanticObjectId(str(insert_result.inserted_id))

    # Add fridge ID to user's fridge_ids
    updated_user = users.find_one_and_update(
    {"email": email},
    {"$push": {"fridge_ids": fridge.id}},
    return_document=ReturnDocument.AFTER,
    )
    if updated_user:  # Successfully added foods
        print(f"Added ID to {email}'s account")
    else:
        print("User not found!")

    return fridge.to_json()

# Retrieve fridge from given ID
"""
Success: Returns JSON representation of Fridge
Failure: 404
"""
@app.route("/api/fridge/<string:id>", methods=["GET"])
def get_fridge(id):
    if len(id) != 24:
        flask.abort(404, "fridge not found")
    fridge = get_fridge_mongodb(id)
    return fridge.to_json()

# Add or remove user of fridge
"""
Expects
{
    "email": "",
    "name": "",
    "action": "remove/add"
}

Returns email of user that was added to fridge
"""
@app.route("/api/fridge/<string:id>/users", methods=["PUT"])
def update_fridge_users(id):
    request_json = request.get_json()
    email = request_json["email"]
    action = request_json["action"]
    if action == "add":
        updated_fridge = fridges.find_one_and_update(
        {"_id": PydanticObjectId(id)},
        {"$push": {"users": email}},
        return_document=ReturnDocument.AFTER,
        )
        if updated_fridge:  # Successfully added user
            return email
        else:
            flask.abort(404, "Fridge not found")
    elif action == "remove":
        updated_fridge = fridges.find_one_and_update(
        {"_id": PydanticObjectId(id)},
        {"$pull": {"users": email}},
        return_document=ReturnDocument.AFTER,
        )
        if updated_fridge:  # Successfully removed user
            return email
        else:
            flask.abort(404, "Fridge not found")
    else:
        flask.abort(400, "Invalid action")

"""
EXPECTS
{
    "foods": [],
    "action": "add"/"remove",
}

Slug field should be set to the food name with dashes in between
If action == "remove",  pass in food names/slugs instead of entire food objects in the request body
"""
@app.route("/api/fridge/<string:id>/foods", methods=["PUT"])
def add_to_fridge(id):
    request_json = request.get_json()
    action = request_json["action"]
    foods_raw = request_json["foods"]
    foods = json.loads(foods_raw)   # Parse food objects
    if action == 'add':
        for food in foods:
            food['_id'] = uuid4()
        food_list = [Food(**food).to_bson() for food in foods]    # Convert JSON foods to food objects for mongodb
        updated_fridge = fridges.find_one_and_update(
        {"_id": PydanticObjectId(id)},
        {"$addToSet": {"foods": {"$each": food_list}}},
        return_document=ReturnDocument.AFTER,
        )
        if updated_fridge:  # Successfully added foods
            return food_list
        else:
            flask.abort(404, "Fridge not found")
    elif action == 'remove':
        food_list = foods
        # Remove foods included in request body
        print(food_list)
        for food in food_list:
            updated_fridge = fridges.find_one_and_update(
            {"_id": PydanticObjectId(id)},
            { "$pull": { "foods": { "slug": food['slug'], 'expiration_date': food['expiration_date'] } } },
            return_document=ReturnDocument.AFTER,
            )
        if updated_fridge:  # Successfully removed foods
            return food_list
    else:
        flask.abort(400, "Invalid action")


# Get/modify information about a specific food in the fridge
"""
PUT EXPECTS
Food object

RETURNS
Food object:
{
    "name":
    "category":
    "location":
    ...
}
"""
@app.route("/api/fridge/<string:id>/foods/<string:slug>", methods=["GET", "PUT"])
def get_food(id, slug):
    fridge: Fridge = get_fridge_mongodb(id)
    foods = fridge.foods
    filtered_foods = list(filter(lambda x : x.slug == slug, foods))
    if request.method == "GET":
        return filtered_foods[0].to_json()
    elif request.method == "PUT":
        # TODO: Remove and reinsert food
        print("replacing food")

    else:
        flask.abort(400, "Invalid request")


# Delete entire fridge
@app.route("/api/fridge/<string:id>", methods=["DELETE"])
def delete_food(id):
    id_object: PydanticObjectId = PydanticObjectId(id)
    deleted_fridge = fridges.find_one_and_delete(
        {"_id": id_object},
    )

    if deleted_fridge:
        # Remove IDs from associated users
        fridge: Fridge = Fridge(**deleted_fridge)
        emails = fridge.users
        for email in emails:
            updated_fridge = users.find_one_and_update(
            {"email": email},
            {"$pull": {"fridge_ids": id_object}},
            return_document=ReturnDocument.AFTER,
            )
            if updated_fridge:  # Successfully removed user
                print(f"Removed fridge {id} from {email}'s account")
            else:
                print(f"No account found for {email}")
        return Fridge(**deleted_fridge).to_json()
    else:
        flask.abort(404, "Fridge not found")
        
# Retrieve fridge object reference from given ObjectId
def get_fridge_mongodb(id) -> Fridge:
    id_object: PydanticObjectId = PydanticObjectId(id)
    raw_fridge = fridges.find_one_or_404(id_object)
    fridge: Fridge = Fridge(**raw_fridge)
    return fridge

def get_user_mongodb(email: str) -> User:
    raw_user = users.find_one({"email": email})
    user: User = User(**raw_user)
    return user

# # Route to display recommended recipes
@app.route('/api/fridge/<string:id>/recommended_recipes', methods=['GET'])
def get_recommended_recipes(id):
    category = request.args.get('category')
    recommended_recipes = recommend_recipes(id, category)
    return recommended_recipes

# Function to get user's ingredients from MongoDB
def get_fridge_ingredients(id):
    fridge = fridges.find_one({"_id": PydanticObjectId(id)})
    if fridge:
        fridge_ingredients = fridge.get('foods', [])
        food_names = [item['name'] for item in fridge_ingredients]
        return food_names
    else:
        return []

# Function to recommend recipes based on user ingredients
def recommend_recipes(id, category):
    food_names = get_fridge_ingredients(id)
    if food_names:
        
        recipes = recipes_collection.find()
        print(category)
        if (category != "All"):
            if (category == "Snacks"):
                category = "snack"
            if (category == "Drinks"):
                category = "drink"
            recipes = recipes_collection.find({'category': category.lower()})

        # Sorting by highest number of matching ingredients
        # Omits zero matching ingredients
        # sorted_recipes = sorted(
        #     (recipe for recipe in recipes if any(ingredient['ingredient'] in food_names for ingredient in recipe['ingredients'])),
        #     key=lambda x: sum(ingredient['ingredient'] in food_names for ingredient in x['ingredients']),
        #     reverse=True,
        # )

        # Sorted by least number of missing ingredients to make recipe
        # Omits zero matching ingredients
        sorted_recipes = sorted(
            (recipe for recipe in recipes if any(ingredient['ingredient'] in food_names for ingredient in recipe['ingredients'])),
            key=lambda x: len(set(ingredient['ingredient'] for ingredient in x['ingredients']) - set(food_names)),
        )

        filtered_recipes = [recipe for recipe in sorted_recipes if len(set(ingredient['ingredient'] for ingredient in recipe['ingredients']) - set(food_names)) <= 4]

        for recipe in filtered_recipes:
            recipe['_id'] = str(recipe['_id'])
        return filtered_recipes
    else:
        return ['No recipes with matching ingredients :(']

# Route for recipe details page
@app.route('/api/fridge/<string:id>/recipes/<string:recipe_id>', methods=['GET'])
def recipe_details(id, recipe_id):
    recipe = recipes_collection.find_one({'_id': PydanticObjectId(recipe_id)})
    recipe['_id'] = str(recipe['_id'])
    return jsonify(recipe=recipe)

# Route to receive servings data and update fridge ingredients
@app.route('/api/fridge/<string:id>/recipes/<string:recipe_id>/servings', methods=['POST'])
def update_fridge_servings(id, recipe_id):
    request_data = request.get_json()
    servings = request_data.get('servings', 1)  # Default servings is 1 if not provided
    try:
        servings = int(servings)
    except ValueError:
        return jsonify(error='Servings must be a number'), 400

    # Find the matching recipe in recipes_collection
    recipe = recipes_collection.find_one({'_id': PydanticObjectId(recipe_id)})
    if not recipe:
        return jsonify(error='Recipe not found'), 404

    # Adjust ingredient quantities in the fridge based on servings
    fridge = fridges.find_one({"_id": PydanticObjectId(id)})
    if not fridge:
        return jsonify(error='Fridge not found'), 404

    fridge_ingredients = fridge.get('foods', [])
    updated_fridge_ingredients = []  # Initialize list for updated fridge ingredients

    for ingredient in recipe['ingredients']:
        ingredient_name = ingredient['ingredient']
        ingredient_amount = ingredient['amount']
        amount_used = ingredient_amount * servings
        for fridge_item in fridge_ingredients:
            if fridge_item['name'] == ingredient_name:
                quantity = int(fridge_item['quantity'])
                if amount_used < quantity:  # Check if recipe amount is less than fridge quantity
                    fridge_item['quantity'] = str(quantity - amount_used)  # Update quantity if enough in fridge
                    updated_fridge_ingredients.append(fridge_item)  # Append the updated fridge item
                break  # Found matching ingredient, no need to check others

    # Include fridge items not updated (amount_used >= quantity)
    for fridge_item in fridge_ingredients:
        if fridge_item not in updated_fridge_ingredients:
            updated_fridge_ingredients.append(fridge_item)

    # Update fridge with adjusted ingredient quantities
    updated_fridge = fridges.find_one_and_update(
        {"_id": PydanticObjectId(id)},
        {"$set": {"foods": updated_fridge_ingredients}},
        return_document=ReturnDocument.AFTER,
    )

    if updated_fridge:
        return jsonify(message='Fridge ingredients updated successfully'), 200
    else:
        return jsonify(error='Failed to update fridge ingredients'), 500