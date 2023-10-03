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
        row = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).fetchone()
        num_red_ml = row[1]
        gold = row[2]

        # add ml and pay gold for every barrel delivered 
        for barrel in barrels_delivered:
            num_red_ml += barrel.ml_per_barrel * barrel.quantity
            gold -= barrel.price 
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = {}".format(gold)))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = {}".format(num_red_ml)))
        
    return "OK"

# Gets called once a day
# purchase a new small red potion barrel only if the number of potions in inventory is less than 10. 
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    
    with db.engine.begin() as connection:
        row = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).fetchone()
        num_red_potions = row[0]
        gold = row[2]

        if num_red_potions >= 10:
            return []

        # purchase one small red barrel if i can afford it
        for barrel in wholesale_catalog:
            if barrel.price < gold and barrel.sku == "SMALL_RED_BARREL":
                return [
                    {
                        # "sku": "SMALL_RED_BARREL",
                        "sku": barrel.sku,
                        "quantity": 1,
                    }
                ]
       
        # return none because there are none available in catalog OR i can't afford
        return []


