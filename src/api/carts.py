from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        id = connection.execute(sqlalchemy.text("INSERT INTO carts DEFAULT VALUES RETURNING *")).scalar_one()
    
    print("CREATE CART: new cart id", id)
    return {"cart_id": id}
        

@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    with db.engine.begin() as connection:
        # Check if item already exists in cart
        cart = connection.execute(
                sqlalchemy.text("""
                                    SELECT cart_id, potions_id 
                                    FROM cart_items 
                                    WHERE cart_id = :cart_id AND potions_id = 
                                    (SELECT id FROM potions WHERE potions.sku = :item_sku)
                                """), 
                [{"cart_id": cart_id, "item_sku": item_sku}]).fetchone()
        
        # Add to cart if it doesn't exist already
        if cart is None:
            connection.execute(
                    sqlalchemy.text("""
                                        INSERT INTO cart_items (cart_id, quantity, potions_id) 
                                        SELECT :cart_id, :quantity, potions.id 
                                        FROM potions WHERE potions.sku = :item_sku
                                    """),
                    [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])
        # Update quantity in cart if it already exists in cart
        else:
            connection.execute(
                    sqlalchemy.text("""
                                        UPDATE cart_items 
                                        SET quantity = :quantity
                                        WHERE cart_id = :cart_id AND potions_id = (SELECT id FROM potions WHERE potions.sku = :item_sku)
                                    """),
                    [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])

    print("Succesfully added item to cart")
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    potions_bought = 0
    gold_paid = 0

    with db.engine.begin() as connection:
        # get all items in cart 
        items = connection.execute(
                sqlalchemy.text("""
                                    SELECT potions_id, quantity
                                    FROM cart_items
                                    WHERE cart_id = :cart_id
                                """),
                [{"cart_id": cart_id}])
        
        for item in items:
            potion_id = item[0]
            quantity = item[1]
            description = 'Sold ' + str(quantity) + ' id=' + str(potion_id) + ' potions to cart ' + str(cart_id) 
            print(description)
            insert_potion_entry(description, potion_id, -1 * quantity)
            gold = insert_gold_entry(description, potion_id, quantity)
            print("gold paid:", gold)
            
            potions_bought += quantity
            gold_paid += gold
        
        # delete cart after checkout
        connection.execute(sqlalchemy.text("DELETE FROM carts WHERE id = :cart_id"), [{"cart_id": cart_id}])

    print("checkout successful")

    return {
        "total_potions_bought": potions_bought,
        "total_gold_paid": gold_paid
    }
        
def insert_potion_entry(description, potion_id, change):
    with db.engine.begin() as connection:
        connection.execute(
                sqlalchemy.text("""
                                INSERT INTO potion_ledger_entries (description, potion_id, change)
                                VALUES
                                (
                                :description, 
                                :potion_id, 
                                :change
                                )
                                """),
                [{"description" : description, "potion_id": potion_id, "change": change}])
        
def insert_gold_entry(description, potion_id, quantity):
    with db.engine.begin() as connection:
        gold_paid = connection.execute(
                sqlalchemy.text("""
                                INSERT INTO gold_ledger_entries (description, change)
                                VALUES
                                (:description, :quantity * (SELECT price FROM potions WHERE :potion_id = potions.id))
                                RETURNING change
                                """),
                [{"description": description, "potion_id" : potion_id, "quantity" : quantity}]).scalar_one()
        
        return gold_paid
        
