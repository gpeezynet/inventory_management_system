import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config.config import Config
from src.utils import logging as app_logging

# Initialize logging
logger = app_logging.get_logger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Import blueprints (to be defined below)
from src.api.routes import api_bp
from src.auth.routes import auth_bp

app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')

@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    db.create_all()
    click.echo("Database initialized.")

if __name__ == '__main__':
    app.run()
