from src.core.inventory.models import Inventory  # Correct

def get_inventory_by_sku(db, sku):
    return Inventory.query.filter_by(sku=sku).first()

def add_inventory(db, item_name, sku, quantity):
    new_item = Inventory(item_name=item_name, sku=sku, quantity=quantity)
    db.session.add(new_item)
    db.session.commit()
    return new_item

def update_inventory_quantity(db, sku, new_quantity):
    item = get_inventory_by_sku(db, sku)
    if item:
        item.quantity = new_quantity
        db.session.commit()
    return item

def remove_inventory(db, sku):
    item = get_inventory_by_sku(db, sku)
    if item:
        db.session.delete(item)
        db.session.commit()
    return item
