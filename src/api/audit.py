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
        globals = connection.execute(sqlalchemy.text("SELECT(num_red_ml + num_green_ml + num_blue_ml + num_dark_ml) AS total_ml, gold FROM global_inventory")).fetchone()
        num_potions = connection.execute(sqlalchemy.text("SELECT SUM(quantity) as total_quantity FROM potions")).scalar_one()

    if globals is not None:
        mls = globals[0]
        gold = globals[1]

    print("AUDIT: number_of_potions", num_potions, "ml_in_barrels", mls, "gold", gold)
    
    return {"number_of_potions": num_potions, "ml_in_barrels": mls, "gold": gold}

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
