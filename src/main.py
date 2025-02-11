from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from config.config import Config
import csv
from io import StringIO, BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import logging

# Import Database & Models
from src.core.db import db  # ✅ Import db from separate module to fix circular import
from src.core.transactions.models import Transaction
from src.core.inventory.models import Inventory
from src.core.inventory.services import create_inventory_item

# Initialize Flask App
app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Needed for flash messages

# Initialize DB
db.init_app(app)  # ✅ Initialize DB here instead of defining it directly

# Register Blueprints
from src.api.routes import api_bp
from src.auth.routes import auth_bp
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')

# Configure Logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# ---------- UI ROUTES ---------- #

@app.route('/')
def index():
    inventory = Inventory.query.all()
    return render_template('index.html', inventory=inventory)

@app.route('/transactions')
@login_required
def transactions():
    transaction_list = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    return render_template('transactions.html', transactions=transaction_list)

@app.route('/reports')
@login_required
def reports():
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    return render_template('reports.html', transactions=transactions)

# ---------- INVENTORY CRUD ROUTES ---------- #

@app.route('/add_item', methods=['POST'])
def add_item():
    item_name = request.form.get('item_name')
    sku = request.form.get('sku')
    quantity = request.form.get('quantity')

    try:
        create_inventory_item(db, item_name, sku, int(quantity))
        flash("Item added successfully!", "success")
    except Exception as e:
        flash(f"Error adding item: {e}", "error")

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

        return redirect(url_for('index'))

    return render_template('edit_item.html', item=item)

@app.route('/delete_item/<int:id>', methods=['POST'])
@login_required
def delete_item(id):
    if not current_user.is_admin():
        flash("Access Denied! Only admins can delete inventory items.", "error")
        return redirect(url_for('index'))

    item = Inventory.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item: {e}', 'error')

    return redirect(url_for('index'))

# ---------- INVENTORY ADJUSTMENT (SALES & RESTOCK) ---------- #

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

# ---------- CSV/PDF EXPORT ROUTES ---------- #

@app.route('/export_csv')
@login_required
def export_csv():
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    output = [["ID", "SKU", "Quantity", "Type", "Timestamp"]]
    
    for transaction in transactions:
        output.append([transaction.id, transaction.sku, transaction.quantity, transaction.transaction_type, transaction.timestamp])

    si = StringIO()
    writer = csv.writer(si)
    writer.writerows(output)

    response = Response(si.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=inventory_report.csv"
    return response

@app.route('/export_pdf')
@login_required
def export_pdf():
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Inventory Report")

    pdf.drawString(100, 750, "Inventory Transaction Report")
    pdf.drawString(100, 735, "----------------------------------")

    y = 720
    for transaction in transactions:
        pdf.drawString(100, y, f"ID: {transaction.id}, SKU: {transaction.sku}, Quantity: {transaction.quantity}, Type: {transaction.transaction_type}, Date: {transaction.timestamp}")
        y -= 15

    pdf.save()
    buffer.seek(0)

    response = Response(buffer.getvalue(), mimetype='application/pdf')
    response.headers["Content-Disposition"] = "attachment; filename=inventory_report.pdf"
    return response

@app.route('/upload_csv', methods=['POST'])
@login_required
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
            if not row.get('item_name') or not row.get('sku') or not row.get('quantity'):
                continue  # Skip invalid rows

            try:
                quantity = int(row['quantity'])
            except ValueError:
                continue  # Skip invalid quantity

            existing_item = Inventory.query.filter_by(sku=row['sku']).first()
            if existing_item:
                existing_item.quantity += quantity
            else:
                new_item = Inventory(item_name=row['item_name'], sku=row['sku'], quantity=quantity)
                db.session.add(new_item)

        db.session.commit()
        flash('CSV processed successfully!', 'success')
        app.logger.info('CSV file processed successfully')

    except Exception as e:
        db.session.rollback()
        flash(f'Error processing CSV: {e}', 'error')
        app.logger.error(f'Error processing CSV: {e}')
    
    return redirect(url_for('index'))

# ---------- RUN APPLICATION ---------- #
if __name__ == '__main__':
    app.run()
