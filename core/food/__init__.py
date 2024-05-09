from flask import Blueprint

food = Blueprint('food', __name__, template_folder='templates')

from . import views
from .models import Food, Entry