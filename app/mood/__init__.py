from flask import Blueprint

mood_bp = Blueprint('mood', __name__, url_prefix='/mood')

from app.mood import routes
