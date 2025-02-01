from flask import Blueprint, jsonify, request
from src.main import db
from src.core.inventory.services import (
    create_inventory_item,
    adjust_inventory_quantity,
    delete_inventory_item
)

api_bp = Blueprint('api', __name__)

@api_bp.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Inventory API"})

@api_bp.route('/inventory', methods=['POST'])
def add_inventory():
    data = request.get_json()
    try:
        item = create_inventory_item(
            db,
            item_name=data['item_name'],
            sku=data['sku'],
            quantity=data.get('quantity', 0)
        )
        return jsonify({'message': 'Inventory item created', 'sku': item.sku}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/inventory/<sku>', methods=['PUT'])
def update_inventory(sku):
    data = request.get_json()
    try:
        delta = int(data.get('delta', 0))
        adjust_inventory_quantity(db, sku, delta)
        return jsonify({'message': 'Inventory updated', 'sku': sku})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/inventory/<sku>', methods=['DELETE'])
def remove_inventory(sku):
    try:
        delete_inventory_item(db, sku)
        return jsonify({'message': 'Inventory item removed', 'sku': sku})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

