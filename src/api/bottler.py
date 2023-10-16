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
        row = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory")).fetchone()

        if row is not None:
            num_red_ml = row[0]
            num_green_ml = row[1]
            num_blue_ml = row[2]
            num_dark_ml = row[3]

        # print how many potions
        potions = connection.execute(sqlalchemy.text("SELECT sku, quantity FROM potions")).fetchall()
        print("Bottlers delivered BEFORE")
        for potion in potions:
            print(potion[0], potion[1])

        for potion in potions_delivered:
            num_red_ml -= potion.potion_type[0] * potion.quantity
            num_green_ml -= potion.potion_type[1] * potion.quantity
            num_blue_ml -= potion.potion_type[2] * potion.quantity
            num_dark_ml -= potion.potion_type[3] * potion.quantity
            print("Bottlers delivered:", potion.quantity, potion.potion_type)
            connection.execute(
                sqlalchemy.text("""
                                UPDATE potions 
                                SET quantity = quantity + :additional_quantity
                                WHERE potion_type = :potion_type
                                """),
                [{"additional_quantity": potion.quantity, "potion_type": potion.potion_type}])

        connection.execute(
            sqlalchemy.text("""
                            UPDATE global_inventory SET 
                            num_red_ml = :num_red_ml, 
                            num_green_ml = :num_green_ml, 
                            num_blue_ml = :num_blue_ml,
                            num_dark_ml = :num_dark_ml
                            """),
            [{"num_red_ml": num_red_ml, "num_green_ml": num_green_ml, "num_blue_ml": num_blue_ml, "num_dark_ml": num_dark_ml}])
        
        # print how many potionss
        potions = connection.execute(sqlalchemy.text("SELECT sku, quantity FROM potions")).fetchall()
        print("Bottlers delivered AFTER")
        for potion in potions:
            print(potion[0], potion[1])

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
    # for potion in potions:
    #     quantity = 0
    #     potion_type = potion[1]
    #     # gets the recipe of each potion, and ml needed of each type for that potion
    #     needed_red = potion_type[0]
    #     needed_green = potion_type[1]
    #     needed_blue = potion_type[2]
    #     needed_dark = potion_type[3]

    #     while num_red_ml >= needed_red and num_green_ml >= needed_green and num_blue_ml >= needed_blue and num_dark_ml >= needed_dark:
    #         quantity += 1
    #         num_red_ml -= needed_red
    #         num_green_ml -= needed_green
    #         num_blue_ml -= needed_blue
    #         num_dark_ml -= needed_dark
        
    #     plan.append (
    #         {
    #             "potion_type": potion_type,
    #             "quantity": quantity
    #         }
    #     )


    # hardcode purple for now for assignment3
    quantity = 0
    while num_red_ml >= 50 and num_blue_ml >= 50:
        quantity += 1
        num_red_ml -= 50
        num_blue_ml -= 50

    plan.append (
        {
            "potion_type": [50, 0, 50, 0],
            "quantity": quantity
        }
    )

    # hardcode teal for now for assignment3
    quantity = 0
    while num_green_ml >= 50 and num_blue_ml >= 50:
        quantity += 1
        num_green_ml -= 50
        num_blue_ml -= 50

    plan.append (
        {
            "potion_type": [0, 50, 50, 0],
            "quantity": quantity
        }
    )

    # hardcode rest for now for assignment3
    red = int(num_red_ml / 200)
    green = int(num_green_ml / 200)
    blue = int(num_blue_ml / 200)
    plan.append (
        {
            "potion_type": [100, 0, 0, 0],
            "quantity": red
        }
    )
    plan.append (
        {
            "potion_type": [0, 100, 0, 0],
            "quantity": green
        }
    )
    plan.append (
        {
            "potion_type": [0, 0, 100, 0],
            "quantity": blue
        }
    )

    
    print("Bottlers Plan:", plan)

    return plan
