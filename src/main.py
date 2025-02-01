# src/main.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from config.config import Config
import csv
from io import StringIO

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

# CSV Upload Route
@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'csv_file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))
    
    try:
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)

        for row in csv_input:
            # Validate required fields
            if not row.get('item_name') or not row.get('sku') or not row.get('quantity'):
                continue  # Skip rows with missing data
            
            try:
                quantity = int(row['quantity'])  # Convert quantity to an integer
            except ValueError:
                continue  # Skip rows with invalid quantity

            # Check if item exists
            existing_item = Inventory.query.filter_by(sku=row['sku']).first()
            if existing_item:
                existing_item.quantity += quantity  # Update existing quantity
            else:
                new_item = Inventory(
                    item_name=row['item_name'],
                    sku=row['sku'],
                    quantity=quantity
                )
                db.session.add(new_item)
        
        db.session.commit()
        flash('CSV processed successfully!', 'success')
        app.logger.info('CSV file processed successfully')

    except Exception as e:
        db.session.rollback()
        flash(f'Error processing CSV: {e}', 'error')
        app.logger.error(f'Error processing CSV: {e}')
    
    return redirect(url_for('index'))

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
    item = Inventory.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
        app.logger.info(f'Item deleted: {item.id} - {item.item_name}')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item: {e}', 'error')
        app.logger.error(f'Error deleting item {id}: {e}')
    return redirect(url_for('index'))

@app.route('/adjust_inventory', methods=['POST'])
def adjust_inventory():
    sku = request.form.get('sku')
    transaction_type = request.form.get('transaction_type')  # 'sale' or 'restock'
    try:
        quantity = int(request.form.get('quantity'))
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
    except ValueError:
        flash("Invalid quantity entered.", "error")
        return redirect(url_for('index'))

    item = Inventory.query.filter_by(sku=sku).first()
    if not item:
        flash("Item not found.", "error")
        return redirect(url_for('index'))

    if transaction_type == 'sale' and item.quantity < quantity:
        flash("Not enough stock available.", "error")
        return redirect(url_for('index'))

    # Adjust inventory levels
    if transaction_type == 'sale':
        item.quantity -= quantity
    elif transaction_type == 'restock':
        item.quantity += quantity

    # Log transaction
    transaction = Transaction(sku=sku, quantity=quantity, transaction_type=transaction_type)
    db.session.add(transaction)

    try:
        db.session.commit()
        flash(f"{transaction_type.capitalize()} recorded successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error processing transaction: {e}", "error")

    return redirect(url_for('index'))

@app.route('/transactions')
def transactions():
    transaction_list = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    return render_template('transactions.html', transactions=transaction_list)

if __name__ == '__main__':
    app.run()
