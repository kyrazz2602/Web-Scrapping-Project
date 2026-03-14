from tinydb import TinyDB, Query
from datetime import datetime
import os


class Database:
    def __init__(self, db_path="data.json"):
        dirname = os.path.dirname(db_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        self.db = TinyDB(db_path)
        self.products = self.db.table("products")
        self.query = Query()

    def insert_product(self, product_data):
        product_data["created_at"] = datetime.now().isoformat()
        return self.products.insert(product_data)

    def get_product(self, asin):
        return self.products.get(self.query.asin == asin)

    def get_all_products(self):
        return self.products.all()

    def search_products(self, search_criteria):
        q = None
        for key, value in search_criteria.items():
            condition = (self.query[key] == value)
            q = condition if q is None else (q & condition)
        return self.products.search(q) if q else []

    def delete_product(self, asin):
        """Delete a single product by ASIN. Returns number of removed records."""
        return self.products.remove(self.query.asin == asin)

    def delete_products_by(self, search_criteria):
        """Delete all products matching given criteria dict (e.g. parent_asin)."""
        q = None
        for key, value in search_criteria.items():
            condition = (self.query[key] == value)
            q = condition if q is None else (q & condition)
        return self.products.remove(q) if q else []

    def delete_all_products(self):
        """Wipe the entire products table."""
        return self.products.truncate()