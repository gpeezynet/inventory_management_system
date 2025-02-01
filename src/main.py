# src/main.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from config.config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Needed for flash messages
db = SQLAlchemy(app)

# Import your models and services
from src.core.inventory.models import Inventory
from src.core.inventory.services import create_inventory_item

# Existing API blueprint registrations
from src.api.routes import api_bp
from src.auth.routes import auth_bp
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')

# UI Route: Home page that shows inventory
@app.route('/')
def index():
    inventory = Inventory.query.all()
    return render_template('index.html', inventory=inventory)

# UI Route: Handle adding a new inventory item via form POST
@app.route('/add_item', methods=['POST'])
def add_item():
    item_name = request.form.get('item_name')
    sku = request.form.get('sku')
    quantity = request.form.get('quantity')
    error = None
    try:
        # Convert quantity to int and add item using our service
        create_inventory_item(db, item_name, sku, int(quantity))
    except Exception as e:
        error = str(e)
        flash(error, 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()
