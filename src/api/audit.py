from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM gold_ledger_entries")).scalar_one()
        mls = connection.execute(sqlalchemy.text("""
                                                SELECT SUM(change) 
                                                FROM ml_ledger_entries
                                                """)).scalar_one()
        potions = connection.execute(sqlalchemy.text("""
                                                SELECT SUM(change) 
                                                FROM potion_ledger_entries
                                                """)).scalar_one()
        if potions is None:
            potions = 0

    print("AUDIT: number_of_potions", potions, "ml_in_barrels", mls, "gold", gold)
    
    return {"number_of_potions": potions, "ml_in_barrels": mls, "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
