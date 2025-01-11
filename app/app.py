# app for Flask
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.config import Config
from app.routes import api_bp


migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register routes
    app.register_blueprint(api_bp)

    from app.models import db
    db.init_app(app)  
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001)  # Development server