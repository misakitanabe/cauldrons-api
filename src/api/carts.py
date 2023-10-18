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

# carts = {}
# cart_counter = 0

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
        # Update item quantity in cart if it already exists in cart
        # else:
            

    print("Succesfully added item to cart")
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    with db.engine.begin() as connection:
        old_gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
        print("Cart checkout BEFORE gold:", old_gold)
                                

        # Update potion inventory in potions table
        potions_bought = connection.execute(
                sqlalchemy.text("""
                                    UPDATE potions
                                    SET quantity = potions.quantity - cart_items.quantity
                                    FROM cart_items
                                    WHERE potions.id = cart_items.potions_id and cart_items.cart_id = :cart_id
                                    RETURNING cart_items.quantity;
                                """),
                [{"cart_id": cart_id}]).scalar_one()
        
        # Update gold in global_inventory table
        new_gold = connection.execute(
                sqlalchemy.text("""
                                    UPDATE global_inventory
                                    SET gold = global_inventory.gold + cart_items.quantity * 
                                    (SELECT price FROM potions WHERE (SELECT potions_id FROM cart_items WHERE cart_id = :cart_id) = id)
                                    FROM cart_items
                                    WHERE cart_items.cart_id = :cart_id
                                    RETURNING gold;
                                """),
                [{"cart_id": cart_id}]).scalar_one()
        
        print("Cart checkout AFTER gold:", new_gold)

        # delete cart after checkout
        connection.execute(sqlalchemy.text("DELETE FROM carts WHERE id = :cart_id"), [{"cart_id": cart_id}])

    gold_made = new_gold - old_gold

    print("checkout successful")

    return {
        "total_potions_bought": potions_bought,
        "total_gold_paid": gold_made
    }
        


    # print("cart checkout AFTER: red:", num_red_potions, "green:", num_green_potions, "blue:", num_blue_potions, "gold:", gold)

    # return {"cart checkout AFTER: red:", num_red_potions, "green:", num_green_potions, "blue:", num_blue_potions, "gold:", gold}
