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
        row = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, gold FROM global_inventory")).fetchone()
        if row is not None:
            num_red_ml = row[0]
            num_green_ml = row[1]
            num_blue_ml = row[2]
            gold = row[3]

        print("Barrels delivered BEFORE: red ml:", num_red_ml, "green:", num_green_ml, "blue:", num_blue_ml, "gold:", gold)

        # add ml and pay gold for every barrel delivered 
        for barrel in barrels_delivered:
            if barrel.potion_type == [1, 0, 0, 0]:
                num_red_ml += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0, 1, 0, 0]:
                num_green_ml += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0, 0, 1, 0]:
                num_blue_ml += barrel.ml_per_barrel * barrel.quantity
            gold -= barrel.price 

        print("Barrels delivered AFTER: red ml:", num_red_ml, "green:", num_green_ml, "blue:", num_blue_ml, "gold:", gold)
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = {}, num_red_ml = {}, num_green_ml = {}, num_blue_ml = {}".format(gold, num_red_ml, num_green_ml, num_blue_ml)))
        
    return "OK"

# Gets called once a day
# purchase a new small red potion barrel only if the number of potions in inventory is less than 10. 
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    
    with db.engine.begin() as connection:
        row = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions, gold FROM global_inventory")).fetchone()
        if row is not None:
            num_red_potions = row[0]
            num_green_potions = row[1]
            num_blue_potions = row[2]
            gold = row[3]

        # buys whichever potion has the least stock
        if num_red_potions < num_green_potions and num_red_potions < num_blue_potions:
            least = "SMALL_RED_BARREL"
        elif num_green_potions < num_blue_potions and num_green_potions < num_red_potions:
            least = "SMALL_GREEN_BARREL"
        else:
            least = "SMALL_BLUE_BARREL"

        print("Barrels Plan: Trying to buy", least)
        print("red:", num_red_potions)
        print("green:", num_green_potions)
        print("blue:", num_blue_potions)

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
       
        print("Failed to add to plan:", barrel.sku, "gold:", gold)
        # return none because there are none available in catalog OR i can't afford
        return []


