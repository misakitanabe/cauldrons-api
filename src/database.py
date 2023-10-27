import os
import dotenv
import sqlalchemy

def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")

engine = sqlalchemy.create_engine(database_connection_url(), pool_pre_ping=True)
metadata_obj = sqlalchemy.MetaData()
cart_items = sqlalchemy.Table("cart_items", metadata_obj, autoload_with=engine)
carts = sqlalchemy.Table("carts", metadata_obj, autoload_with=engine)
potions = sqlalchemy.Table("potions", metadata_obj, autoload_with=engine)
potion_ledger_entries = sqlalchemy.Table("potion_ledger_entries", metadata_obj, autoload_with=engine)
gold_ledger_entries = sqlalchemy.Table("gold_ledger_entries", metadata_obj, autoload_with=engine)