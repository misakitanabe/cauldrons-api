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

carts = {}
cart_counter = 0

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    # return {"cart_id": 1}
    global cart_counter
    global carts
    
    cart_counter += 1
    carts[cart_counter] = []
    return {"cart_id": cart_counter}



@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    global cart_counter
    global carts

    for order in carts[cart_id]:
        if order[0] == item_sku:
            order[1] = cart_item.quantity
            return "OK"

    carts[cart_id].append([item_sku, cart_item.quantity])

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    global cart_counter
    global carts

    print("cart_checkout.payment = ", cart_checkout.payment)

    with db.engine.begin() as connection:
        row = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).fetchone()
        num_red_potions = row[0] 
        gold = row[2]
        purchased = carts[cart_id][0][1]

        # only sell to customer if enough in catalog
        if purchased <= num_red_potions:
            num_red_potions -= purchased 
            gold += (purchased * 50)

            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = {}".format(num_red_potions)))
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = {}".format(gold)))

            # remove cart from carts
            carts.pop(cart_id) 

            return {"total_potions_bought": purchased, "total_gold_paid": 50 * purchased}
    
    return {"total_potions_bought": 0, "total_gold_paid": 0}
