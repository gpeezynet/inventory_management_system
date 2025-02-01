from flask import Blueprint, jsonify

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET'])
def login():
    return jsonify({"message": "Auth route placeholder"})
