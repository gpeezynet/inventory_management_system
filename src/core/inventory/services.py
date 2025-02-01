from src.core.inventory.repositories import (
    add_inventory,
    update_inventory_quantity,
    remove_inventory,
    get_inventory_by_sku
)

def create_inventory_item(db, item_name, sku, quantity):
    if get_inventory_by_sku(db, sku):
        raise ValueError("Item with this SKU already exists.")
    return add_inventory(db, item_name, sku, quantity)

def adjust_inventory_quantity(db, sku, delta):
    item = get_inventory_by_sku(db, sku)
    if not item:
        raise ValueError("Item not found.")
    new_quantity = item.quantity + delta
    if new_quantity < 0:
        raise ValueError("Insufficient stock.")
    return update_inventory_quantity(db, sku, new_quantity)

def delete_inventory_item(db, sku):
    return remove_inventory(db, sku)
