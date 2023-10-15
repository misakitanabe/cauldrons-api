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
        row = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions, num_red_ml, num_green_ml, num_blue_ml FROM global_inventory")).fetchone()
        if row is not None:
            num_red_potions = row[0]
            num_green_potions = row[1]
            num_blue_potions = row[2]
            num_red_ml = row[3]
            num_green_ml = row[4]
            num_blue_ml = row[5]
        print("Bottlers delivered BEFORE: red:", num_red_potions, "green:", num_green_potions, "blue:", num_blue_potions)

        for potion in potions_delivered:
            if potion.potion_type == [100, 0, 0, 0]:
                num_red_potions += potion.quantity
                num_red_ml -= (potion.quantity * 100)
            elif potion.potion_type == [0, 100, 0, 0]:
                num_green_potions += potion.quantity
                num_green_ml -= (potion.quantity * 100)
            elif potion.potion_type == [0, 0, 100, 0]:
                num_blue_potions += potion.quantity
                num_blue_ml -= (potion.quantity * 100)

        print("Bottlers delivered AFTER: red:", num_red_potions, "green:", num_green_potions, "blue:", num_blue_potions)

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = {}, num_green_potions = {}, num_blue_potions = {}".format(num_red_potions, num_green_potions, num_blue_potions)))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = {}, num_green_ml = {}, num_blue_ml = {}".format(num_red_ml, num_green_ml, num_blue_ml)))

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
        row = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory")).fetchone()
        if row is not None:
            num_red_ml = row[0]
            num_green_ml = row[1]
            num_blue_ml = row[2]
            num_dark_ml = row[3]

        potions = connection.execute(sqlalchemy.text("SELECT quantity, potion_type FROM potions ORDER BY quantity ASC")).fetchall()
        
    plan = []
    
    # creates bottle plan for each potion starting from ones with lowest stock, as they were ordered ascendingly by quantity
    for potion in potions:
        quantity = 0
        potion_type = potion[1]
        # gets the recipe of each potion, and ml needed of each type for that potion
        needed_red = potion_type[0]
        needed_green = potion_type[1]
        needed_blue = potion_type[2]
        needed_dark = potion_type[3]

        while num_red_ml >= needed_red and num_green_ml >= needed_green and num_blue_ml >= needed_blue and num_dark_ml >= needed_dark:
            quantity += 1
            num_red_ml -= needed_red
            num_green_ml -= needed_green
            num_blue_ml -= needed_blue
            num_dark_ml -= needed_dark
        
        plan.append (
            {
                "potion_type": potion_type,
                "quantity": quantity
            }
        )
    
    print("Bottlers Plan:", plan)

    return plan


        # red_count = int(num_red_ml / 100)
        # green_count = int(num_green_ml / 100)
        # blue_count = int(num_blue_ml / 100)

        # # Append potions to purchase to plan if planning to buy one or more
        # plan = []
        # if red_count > 0:
        #     plan.append(
        #         {
        #             "potion_type": [100, 0, 0, 0],
        #             "quantity": red_count,
        #         }
        #     )
        # if green_count > 0:
        #     plan.append(
        #         {
        #             "potion_type": [0, 100, 0, 0],
        #             "quantity": green_count,
        #         }
        #     )
        # if blue_count > 0:
        #     plan.append(
        #         {
        #             "potion_type": [0, 0, 100, 0],
        #             "quantity": blue_count,
        #         }
        #     )

    # print("Bottlers Plan:", plan)

    # return plan
