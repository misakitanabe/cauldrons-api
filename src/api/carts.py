from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
# from src.database import cart_items
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    limit = 5
    # prev = '0'
    if search_page != '':
        offset = (int)(search_page)
        next = (search_page)
    else:
        offset = 0
        next = ""

    # set order_by based on sort_col
    if sort_col is search_sort_options.customer_name:
        order_by = db.carts.c.customer_name
    elif sort_col is search_sort_options.item_sku:
        order_by = db.potions.c.sku
    elif sort_col is search_sort_options.line_item_total:
        order_by = db.cart_items.c.quantity
    elif sort_col is search_sort_options.timestamp:
        order_by = db.potion_ledger_entries.c.created_at
    else:
        assert False

    # set order_by based on sort_order
    if sort_order == search_sort_order.desc:
        if sort_col is search_sort_options.line_item_total:
            order_by = sqlalchemy.asc(order_by)
        else:
            order_by = sqlalchemy.desc(order_by)
    else:
        if sort_col is search_sort_options.line_item_total:
            order_by = sqlalchemy.desc(order_by)
        else:
            order_by = sqlalchemy.asc(order_by)

    # create query
    stmt = (
        sqlalchemy.select(
            db.cart_items.c.id,
            db.potions.c.sku,
            db.carts.c.customer,
            db.cart_items.c.quantity,
            db.potion_ledger_entries.c.created_at
        )
        .join(db.potions, db.potions.c.id == db.cart_items.c.potions_id)
        .join(db.carts, db.carts.c.id == db.cart_items.c.cart_id)
        .join(db.potion_ledger_entries, db.potion_ledger_entries.c.cart_items_id == db.cart_items.c.id)
        .limit(limit)
        .offset(offset)
        .order_by(order_by) 
    )

    # filter only if name parameter is passed
    if customer_name != "":
        stmt = stmt.where(db.carts.c.customer.ilike(f"%{customer_name}%"))

    # filter only if potion_sku parameter is passed
    if potion_sku != "":
        stmt = stmt.where(db.potions.c.sku.ilike(f"%{potion_sku}%"))

    # execute transaction
    with db.engine.connect() as conn:
        results = []
        res = conn.execute(stmt)

        for i, row in enumerate(res):
            if i < 5:
                results.append(
                    {
                        "line_item_id": row.id,
                        "item_sku": row.sku,
                        "customer_name": row.customer,
                        "line_item_total": row.quantity,
                        "timestamp": row.created_at
                    }
                )
            else:
                if next == "":
                    next = '0'
                next = (int)(next) + 5

        return {
            "previous": "",
            "next": next,
            "results": results
        }


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        id = connection.execute(
            sqlalchemy.text("""
                            INSERT INTO carts (id, customer) 
                            VALUES
                            (DEFAULT, :name)
                            RETURNING id;
                            """),
            [{"name": new_cart.customer}]).scalar_one()
    
    print("CREATE CART: new cart id", id)
    return {"cart_id": id}
        

@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    with db.engine.begin() as connection:
        # Check if item already exists in cart
        cart = connection.execute(
                sqlalchemy.text("""
                                    SELECT cart_id, potions_id 
                                    FROM cart_items 
                                    WHERE cart_id = :cart_id AND potions_id = 
                                    (SELECT id FROM potions WHERE potions.sku = :item_sku)
                                """), 
                [{"cart_id": cart_id, "item_sku": item_sku}]).fetchone()
        
        # Add to cart if it doesn't exist already
        if cart is None:
            connection.execute(
                    sqlalchemy.text("""
                                        INSERT INTO cart_items (cart_id, quantity, potions_id) 
                                        SELECT :cart_id, :quantity, potions.id 
                                        FROM potions WHERE potions.sku = :item_sku
                                    """),
                    [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])
        # Update quantity in cart if it already exists in cart
        else:
            connection.execute(
                    sqlalchemy.text("""
                                        UPDATE cart_items 
                                        SET quantity = :quantity
                                        WHERE cart_id = :cart_id AND potions_id = (SELECT id FROM potions WHERE potions.sku = :item_sku)
                                    """),
                    [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])

    print("Succesfully added item to cart")
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    potions_bought = 0
    gold_paid = 0

    with db.engine.begin() as connection:
        # get all items in cart 
        items = connection.execute(
                sqlalchemy.text("""
                                    SELECT potions_id, quantity, id
                                    FROM cart_items
                                    WHERE cart_id = :cart_id
                                """),
                [{"cart_id": cart_id}])
        
        for item in items:
            potion_id = item[0]
            quantity = item[1]
            cart_items_id = item[2]
            description = 'Sold ' + str(quantity) + ' id=' + str(potion_id) + ' potions to cart ' + str(cart_id) 
            print(description)
            insert_potion_entry(description, potion_id, -1 * quantity, cart_items_id)
            gold = insert_gold_entry(description, potion_id, quantity, cart_items_id)
            print("gold paid:", gold)
            
            potions_bought += quantity
            gold_paid += gold
        
        # delete cart after checkout
        # connection.execute(sqlalchemy.text("DELETE FROM carts WHERE id = :cart_id"), [{"cart_id": cart_id}])

    print("checkout successful")

    return {
        "total_potions_bought": potions_bought,
        "total_gold_paid": gold_paid
    }
        
def insert_potion_entry(description, potion_id, change, cart_items_id):
    with db.engine.begin() as connection:
        connection.execute(
                sqlalchemy.text("""
                                INSERT INTO potion_ledger_entries (description, potion_id, change, cart_items_id)
                                VALUES
                                (
                                :description, 
                                :potion_id, 
                                :change,
                                :cart_items_id
                                )
                                """),
                [{"description" : description, "potion_id": potion_id, "change": change, "cart_items_id": cart_items_id}])
        
def insert_gold_entry(description, potion_id, quantity, cart_items_id):
    with db.engine.begin() as connection:
        gold_paid = connection.execute(
                sqlalchemy.text("""
                                INSERT INTO gold_ledger_entries (description, change, cart_items_id)
                                VALUES
                                (:description, :quantity * (SELECT price FROM potions WHERE :potion_id = potions.id), :cart_items_id)
                                RETURNING change
                                """),
                [{"description": description, "potion_id" : potion_id, "quantity" : quantity, "cart_items_id": cart_items_id}]).scalar_one()
        
        return gold_paid
        
