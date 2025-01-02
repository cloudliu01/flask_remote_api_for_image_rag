# app for Flask
from flask import Flask
from app.config import Config
from app.routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register routes
    register_routes(app)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001)  # Development server