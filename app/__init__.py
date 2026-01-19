from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)

    from .routes_participant import bp_participant
    from .routes_admin import bp_admin

    app.register_blueprint(bp_participant)
    app.register_blueprint(bp_admin, url_prefix="/admin")

    return app
