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
        # queries here just for debugging not actually used in updates
        mls = connection.execute(
            sqlalchemy.text("""
                            SELECT SUM(change) 
                            FROM ml_ledger_entries
                            GROUP BY type
                            ORDER BY type ASC
                            """)
            ).fetchall()
        
        if mls is not None:
            num_blue_ml = mls[0][0]
            num_dark_ml = mls[1][0]
            num_green_ml = mls[2][0]
            num_red_ml = mls[3][0]
        
        print("Bottlers delivered BEFORE currently have red ml:", num_red_ml, "green:", num_green_ml, "blue:", num_blue_ml)

        red_diff = 0
        green_diff = 0
        blue_diff = 0
        dark_diff = 0

        for potion in potions_delivered:
            red_diff -= potion.potion_type[0] * potion.quantity
            green_diff -= potion.potion_type[1] * potion.quantity
            blue_diff -= potion.potion_type[2] * potion.quantity
            dark_diff -= potion.potion_type[3] * potion.quantity

            # create new row in potions table for each potion delivered
            description = ('Received ' + str(potion.quantity) + str(potion.potion_type) + 'potions from bottler.')
            print(description)
            insert_potion_entry(description, potion.quantity, potion.potion_type)
            
        # create new transaction and row in ml table for total ml's used
        description = ('Paid bottler ' 
                        + str(red_diff) + ' red mls, ' 
                        + str(green_diff) + ' green mls, '
                        + str(blue_diff) + ' blue mls, '
                        + str(dark_diff) + ' dark mls')
        print(description)

        # update ml by adding row into ml_ledger_entries
        if red_diff < 0:
            insert_ml_entry(description, 'RED', red_diff)

        if green_diff < 0:
            insert_ml_entry(description, 'GREEN', green_diff)

        if blue_diff < 0:
            insert_ml_entry(description, 'BLUE', blue_diff)

        if dark_diff < 0:
            insert_ml_entry(description, 'DARK', dark_diff)

      
        print("Bottlers delivered AFTER currently have red ml:", num_red_ml + red_diff, "green:", num_green_ml + green_diff, "blue:", num_blue_ml + blue_diff)
        

    return "OK"


def insert_potion_entry(description, additional_quantity, potion_type):
    with db.engine.begin() as connection:
        print("INSERTING POTION ROW description:", description)
        connection.execute(
                sqlalchemy.text("""
                                INSERT INTO potion_ledger_entries (description, potion_id, change)
                                VALUES
                                (:description, (SELECT id FROM potions WHERE potion_type = :potion_type), :additional_quantity)
                                """),
                [{"description" : description, "additional_quantity": additional_quantity, "potion_type": potion_type}])
        
        
def insert_ml_entry(description, ml_type, diff):
    with db.engine.begin() as connection:
        connection.execute(
                sqlalchemy.text("""
                                INSERT INTO ml_ledger_entries (description, type, change)
                                VALUES
                                (:description, :ml_type, :diff)
                                """),
                [{"description": description, "ml_type" : ml_type, "diff" : diff}])
   

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    plan = []

    with db.engine.begin() as connection:
        num_potions = connection.execute(
            sqlalchemy.text("""
                            SELECT SUM(change) 
                            FROM potion_ledger_entries
                            """)).scalar_one()
        
        if not num_potions:
            num_potions = 0
        
        if num_potions > 290:
            return []

        # gets number of mls
        mls = connection.execute(
            sqlalchemy.text("""
                            SELECT SUM(change) 
                            FROM ml_ledger_entries
                            GROUP BY type
                            ORDER BY type ASC
                            """)
            ).fetchall()
        
        if mls is not None:
            num_blue_ml = mls[0][0]
            num_dark_ml = mls[1][0]
            num_green_ml = mls[2][0]
            num_red_ml = mls[3][0]

        # gets potion types starting with lowest inventory to high
        potions = connection.execute(
            sqlalchemy.text("""
                            SELECT SUM(entries.change) AS quantity, p.potion_type 
                            FROM potions AS p 
                            LEFT JOIN potion_ledger_entries AS entries ON p.id = entries.potion_id
                            GROUP BY p.id
                            ORDER BY quantity ASC
                            """)
            ).fetchall()

    print("Bottlers Plan currently have red ml:", num_red_ml, "green:", num_green_ml, "blue:", num_blue_ml)

    # creates bottle plan for each potion starting from ones with lowest stock, as they were ordered ascendingly by quantity
    for potion in potions:
        quantity = 0
        potion_type = potion[1]
        # DON'T MAKE TEAL OR PURPLE
        if potion_type != [0,50,50,0] and potion_type != [50,0,50,0] and num_potions < 295:
            # gets the recipe of each potion, and ml needed of each type for that potion
            needed_red = potion_type[0]
            needed_green = potion_type[1]
            needed_blue = potion_type[2]
            needed_dark = potion_type[3]

            while quantity < 100 and num_red_ml >= needed_red and num_green_ml >= needed_green and num_blue_ml >= needed_blue and num_dark_ml >= needed_dark:
                quantity += 1
                num_red_ml -= needed_red
                num_green_ml -= needed_green
                num_blue_ml -= needed_blue
                num_dark_ml -= needed_dark
                num_potions += 1
                if num_potions > 295:
                    break
            
            if quantity > 0:
                plan.append (
                    {
                        "potion_type": potion_type,
                        "quantity": quantity
                    }
                )

    print("Bottlers Plan:", plan)

    return plan
