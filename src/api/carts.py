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

    print("Carts set_item_quantity:", cart_item, "for", item_sku, "cart-id:", cart_id)

    # if item to set the quantity of already exists in cart, update the quantity to new quantity in cart_item
    for order in carts[cart_id]:
        if order[0] == item_sku:
            order[1] = cart_item.quantity
            print("Succesfully updated quantity of item")
            return "OK"

    # else, adds that item to cart with quantity in cart_item
    carts[cart_id].append([item_sku, cart_item.quantity])
    print("Succesfully added item to cart")
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
        row = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions, gold FROM global_inventory")).fetchone()
        if row is not None:
            num_red_potions = row[0]
            num_green_potions = row[1]
            num_blue_potions = row[2]
            gold = row[3]

        print("cart checkout BEFORE: red:", num_red_potions, "green:", num_green_potions, "blue:", num_blue_potions, "gold:", gold)

        # update potion count and gold for every item in their cart
        for item in carts[cart_id]:
            if item[0] == "RED_POTION_0":
                print("carts checkout: customer wants", item[1], item[0], "potions and i have", num_red_potions, "potions")
                
                # only sell to customer if enough in catalog
                if item[1] <= num_red_potions:
                    num_red_potions -= item[1]
                    gold += (item[1] * 25) 
                    print("Success selling", item[1], "red potions")
            
            elif item[0] == "GREEN_POTION_0":
                print("carts checkout: customer wants", item[1], item[0], "potions and i have", num_green_potions, "potions")
                
                # only sell to customer if enough in catalog
                if item[1] <= num_green_potions:
                    num_green_potions -= item[1]
                    gold += (item[1] * 25) 
                    print("Success selling", item[1], "green potions")

            elif item[0] == "BLUE_POTION_0":
                print("carts checkout: customer wants", item[1], item[0], "potions and i have", num_blue_potions, "potions")
                
                # only sell to customer if enough in catalog
                if item[1] <= num_blue_potions:
                    num_blue_potions -= item[1]
                    gold += (item[1] * 25) 
                    print("Success selling", item[1], "blue potions")

            # update database 
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = {}, num_green_potions = {}, num_blue_potions = {}, gold = {}".format(num_red_potions, num_green_potions, num_blue_potions, gold)))

    # remove cart from carts
    carts.pop(cart_id) 

    print("cart checkout AFTER: red:", num_red_potions, "green:", num_green_potions, "blue:", num_blue_potions, "gold:", gold)

    return {"cart checkout AFTER: red:", num_red_potions, "green:", num_green_potions, "blue:", num_blue_potions, "gold:", gold}
