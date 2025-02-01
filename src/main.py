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

import logging

# Configure logging: this will log messages to 'app.log' file.
logging.basicConfig(
    filename='app.log',         # Log file name
    level=logging.INFO,         # Minimum level of messages to log (INFO and above)
    format='%(asctime)s %(levelname)s: %(message)s'  # Format for each log entry
)

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

@app.route('/edit_item/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    item = Inventory.query.get_or_404(id)
    if request.method == 'POST':
        item.item_name = request.form.get('item_name')
        item.sku = request.form.get('sku')
        try:
            item.quantity = int(request.form.get('quantity'))
        except ValueError:
            flash('Quantity must be an integer.', 'error')
            return redirect(url_for('edit_item', id=id))
        try:
            db.session.commit()
            flash('Item updated successfully!', 'success')
            app.logger.info(f'Item updated: {item.id} - {item.item_name}')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating item: {e}', 'error')
            app.logger.error(f'Error updating item {id}: {e}')
        return redirect(url_for('index'))
    return render_template('edit_item.html', item=item)

@app.route('/delete_item/<int:id>', methods=['POST'])
def delete_item(id):
    # Retrieve the item or return a 404 error if it doesn't exist.
    item = Inventory.query.get_or_404(id)
    try:
        # Attempt to delete the item from the database.
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
        # Log a success message with item details.
        app.logger.info(f'Item deleted: {item.id} - {item.item_name}')
    except Exception as e:
        # Rollback any changes if there's an error.
        db.session.rollback()
        flash(f'Error deleting item: {e}', 'error')
        # Log an error message with the exception details.
        app.logger.error(f'Error deleting item {id}: {e}')
    # Redirect back to the index page.
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()
