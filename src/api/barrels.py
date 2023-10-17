from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    with db.engine.begin() as connection:
        row = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold FROM global_inventory")).fetchone()
        if row is not None:
            num_red_ml = row[0]
            num_green_ml = row[1]
            num_blue_ml = row[2]
            num_dark_ml = row[3]
            gold = row[4]

        print("Barrels delivered BEFORE: red ml:", num_red_ml, "green:", num_green_ml, "blue:", num_blue_ml, "dark:", num_dark_ml, "gold:", gold)

        # add ml and pay gold for every barrel delivered 
        for barrel in barrels_delivered:
            if barrel.potion_type == [1, 0, 0, 0]:
                num_red_ml += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0, 1, 0, 0]:
                num_green_ml += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0, 0, 1, 0]:
                num_blue_ml += barrel.ml_per_barrel * barrel.quantity
            else:
                num_dark_ml += barrel.ml_per_barrel * barrel.quantity
            gold -= barrel.price 

        print("Barrels delivered AFTER: red ml:", num_red_ml, "green:", num_green_ml, "blue:", num_blue_ml, "gold:", gold)
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = {}, num_red_ml = {}, num_green_ml = {}, num_blue_ml = {}, num_dark_ml = {}".format(gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml)))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
        potion_row = connection.execute(sqlalchemy.text("SELECT potion_type FROM potions ORDER BY quantity ASC")).fetchone()

        if potion_row is not None:
            least_type = potion_row[0]
            least_index = least_type.index(max(least_type))
            if least_index == 0:
                least = "SMALL_RED_BARREL"
            elif least_index == 1:
                least = "SMALL_GREEN_BARREL"
            else:
                least = "SMALL_BLUE_BARREL"
            #     
            # if least_type == [100, 0, 0, 0]:
            #     least = "SMALL_RED_BARREL"
            # elif least_type == [0, 100, 0, 0]:
            #     least = "SMALL_GREEN_BARREL"
            # else:
            #     least = "SMALL_BLUE_BARREL"

        # DELETE LATER HARDCODED FOR NOW
        least = "SMALL_BLUE_BARREL"

        print("Barrels Plan: Trying to buy", least)

    # purchase one small barrel if i can afford it
    for barrel in wholesale_catalog:
        if barrel.price < gold and barrel.sku == least:
            print("Successfully added to plan:", barrel.sku)
            return [
                {
                    "sku": barrel.sku,
                    "quantity": 1,
                }
            ]
    
    # DELETE LATER BUYS MINI BLUE FOR NOW
    for barrel in wholesale_catalog:
        if barrel.sku == "MINI_BLUE_BARREL" and barrel.price < gold:
            print("Successfully added to plan:", barrel.sku)
            return [
                {
                    "sku": barrel.sku,
                    "quantity": 1,
                }
            ]
     
    
    print("Failed to add to plan:", barrel.sku, "gold:", gold)
    # return none because there are none available in catalog OR i can't afford
    return []


