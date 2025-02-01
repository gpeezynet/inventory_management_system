from src.main import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'sale' or 'restock'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Transaction {self.sku} - {self.transaction_type} ({self.quantity})>"
