from src.main import db

class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<Inventory {self.sku} - {self.item_name}>"

def add_inventory(db, item_name, sku, quantity):
    new_item = Inventory(item_name=item_name, sku=sku, quantity=quantity)
    db.session.add(new_item)
    db.session.commit()  # This ensures the item is saved
    return new_item

