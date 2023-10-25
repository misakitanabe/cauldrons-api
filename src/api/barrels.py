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
        # queries here just for debugging not actually used in updates
        gold = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM gold_ledger_entries")).scalar_one()
        ml = connection.execute(sqlalchemy.text("""
                                                SELECT SUM(change) 
                                                FROM ml_ledger_entries
                                                GROUP BY type
                                                ORDER BY type ASC
                                                """)).fetchall()
        if ml is not None:
            num_blue_ml = ml[0][0]
            num_dark_ml = ml[1][0]
            num_green_ml = ml[2][0]
            num_red_ml = ml[3][0]

        print("Barrels delivered BEFORE: red ml:", num_red_ml, "green:", num_green_ml, "blue:", num_blue_ml, "dark:", num_dark_ml, "gold:", gold)

        red_diff = 0
        green_diff = 0
        blue_diff = 0
        dark_diff = 0
        gold_diff = 0

        # add ml and pay gold for every barrel delivered 
        for barrel in barrels_delivered:
            if barrel.potion_type == [1, 0, 0, 0]:
                red_diff += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0, 1, 0, 0]:
                green_diff += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0, 0, 1, 0]:
                blue_diff += barrel.ml_per_barrel * barrel.quantity
            else:
                dark_diff += barrel.ml_per_barrel * barrel.quantity
            gold_diff -= barrel.price 

        print("Barrels delivered AFTER: red ml:", num_red_ml + red_diff, "green:", num_green_ml + green_diff, "blue:", num_blue_ml + blue_diff, "gold:", gold + gold_diff)
       
        # update gold and ml's only if i paid any gold
        if gold_diff < 0:
            description = ('Paid barreler ' + str(gold_diff*-1) + ' gold for '
                            + str(red_diff) + ' red mls, ' 
                            + str(green_diff) + ' green mls, '
                            + str(blue_diff) + ' blue mls, '
                            + str(dark_diff) + ' dark mls')
            print(description)

            # update gold by adding row into gold_ledger_entries
            connection.execute(
                sqlalchemy.text("""
                                INSERT INTO gold_ledger_entries (description, change)
                                VALUES
                                (:description, :gold_diff)
                                """),
                [{"description": description, "gold_diff" : gold_diff}])

            # update ml by adding row into ml_ledger_entries
            if red_diff > 0:
                insert_ml_entry(description, 'RED', red_diff)

            if green_diff > 0:
                insert_ml_entry(description, 'GREEN', green_diff)

            if blue_diff > 0:
                insert_ml_entry(description, 'BLUE', blue_diff)

            if dark_diff > 0:
                insert_ml_entry(description, 'DARK', dark_diff)

    return "OK"


def insert_ml_entry(description, ml_type, diff):
    with db.engine.begin() as connection:
        connection.execute(
                sqlalchemy.text("""
                                INSERT INTO ml_ledger_entries (description, type, change)
                                VALUES
                                (:description, :ml_type, :diff)
                                """),
                [{"description": description, "ml_type" : ml_type, "diff" : diff}])


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    plan = []
    
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM gold_ledger_entries")).scalar_one()
        potion_row = connection.execute(sqlalchemy.text("""
                                                        SELECT potion_type 
                                                        FROM potions AS p 
                                                        LEFT JOIN potion_ledger_entries AS entries ON p.id = entries.potion_id
                                                        GROUP BY p.id
                                                        ORDER BY SUM(entries.change) ASC
                                                        """)).fetchone()

        if potion_row is not None:
            least_type = potion_row[0]
            least_index = least_type.index(max(least_type))
            if least_index == 0:
                least = "LARGE_RED_BARREL"
            elif least_index == 1:
                least = "LARGE_GREEN_BARREL"
            elif least_index == 2:
                least = "LARGE_BLUE_BARREL"
            else:
                least = "LARGE_GREEN_BARREL"

        if gold is None:
            gold = 0
            

        print("Barrels Plan: Trying to buy", least)

    # purchase one small barrel if i can afford it
    for barrel in wholesale_catalog:
        if barrel.sku == least:
            if barrel.price <= gold:
                print("Successfully added to plan:", barrel.sku)
                plan.append(
                    {
                        "sku": barrel.sku,
                        "quantity": 1,
                    }
                )
                if least == "LARGE_RED_BARREL":
                    least = "LARGE_BLUE_BARREL"

                if least == "LARGE_BLUE_BARREL":
                    least = "LARGE_GREEN_BARREL"

                if least == "LARGE_GREEN_BARREL":
                    least = "LARGE_RED_BARREL"

            else:
                print("Not enough gold:", gold)
                least = "MEDIUM_RED_BARREL"
    
    print("Barrels plan:", plan, "gold:", gold)
    return plan


