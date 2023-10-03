from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)

    with db.engine.begin() as connection:
        row = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).fetchone()
        num_red_potions = row[0]

        for potion in potions_delivered:
            if potion.potion_type == [1, 0, 0, 0]:
                num_red_potions += potion.quantity

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = {}".format(num_red_potions)))

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    with db.engine.begin() as connection:
        row = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).fetchone()
        num_red_ml = row[1]
        count = 0

        while num_red_ml >= 100:
            num_red_ml -= 100
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = {}".format(num_red_ml)))
            count += 1

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": count,
            }
        ]
