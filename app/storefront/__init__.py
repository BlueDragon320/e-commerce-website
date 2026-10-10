from flask import Blueprint

storefront = Blueprint('storefront', __name__)

from . import routes
