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
        potions = connection.execute(sqlalchemy.text("""
                                                    SELECT p.sku, p.name, SUM(trans.change) AS quantity, p.price, p.potion_type 
                                                    FROM potions AS p 
                                                    LEFT JOIN potion_ledger_entries AS trans ON p.id = trans.potion_id
                                                    WHERE quantity > 0
                                                    GROUP BY p.id
                                                    """)).fetchall()

        for row in potions:
            catalog.append({
                "sku": row[0],
                "name": row[1],
                "quantity": row[2],
                "price": row[3],
                "potion_type": row[4],
            })
            
    return catalog

   