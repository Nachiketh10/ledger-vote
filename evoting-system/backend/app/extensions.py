"""
Flask extension instances.

Instantiated here (unbound) and attached to the app in app/__init__.py via
.init_app(app). Keeping them in a separate module avoids circular imports
between models, routes, and the app factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)
