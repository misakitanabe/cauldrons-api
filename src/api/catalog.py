from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []

    # Can return a max of 20 items.
    # CALL DATABASE
    with db.engine.begin() as connection:
        row = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions FROM global_inventory")).fetchone()

    if row is not None:
        num_red_potions = row[0]
        num_green_potions = row[1]
        num_blue_potions = row[2]
    
    if num_red_potions > 0:
        catalog.append({
                            "sku": "RED_POTION_0",
                            "name": "red potion",
                            "quantity": num_red_potions,
                            "price": 50,
                            "potion_type": [100, 0, 0, 0],
                        })
    if num_green_potions > 0:
        catalog.append({
                            "sku": "GREEN_POTION_0",
                            "name": "green potion",
                            "quantity": num_green_potions,
                            "price": 50,
                            "potion_type": [0, 100, 0, 0],
                        })
        
    if num_blue_potions > 0:
        catalog.append({
                            "sku": "BLUE_POTION_0",
                            "name": "blue potion",
                            "quantity": num_blue_potions,
                            "price": 60,
                            "potion_type": [0, 0, 100, 0],
                        })
    return catalog
       
