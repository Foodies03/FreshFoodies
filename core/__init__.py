from flask import Flask
from config import Configuration
# from pymongo.collection import Collection

app = Flask(__name__)
app.config.from_object(Configuration)

# blueprint for non-authentication parts of the app
from .food import food as food_blueprint
app.register_blueprint(food_blueprint)

from .receipt import receipt as receipt_blueprint
app.register_blueprint(receipt_blueprint)
from core import views, models  
