# database_setup/backfill_catalogs.py
# Build/refresh the Ingredients and Tags *catalog* tables
# from MealsTable’s JSON and boolean columns. No junction tables.

import json
from sqlalchemy import text
from meal_app import create_app, db
from meal_app.variables import (
    fresh_ingredients as VAR_FRESH,
    tinned_ingredients as VAR_TINNED,
    dry_ingredients as VAR_DRY,
    dairy_ingredients as VAR_DAIRY,
)

TAGS = ['Spring/Summer', 'Autumn/Winter', 'Quick/Easy', 'Special']

def ensure_tags(conn):
    for t in TAGS:
        conn.execute(text("INSERT IGNORE INTO Tags (Tag_Name) VALUES (:t)"), {"t": t})

def upsert_ingredient_name(conn, name: str):
    if not name:
        return
    conn.execute(
        text("INSERT IGNORE INTO Ingredients (Ingredient_Name) VALUES (:n)"),
        {"n": name},
    )

def process_bucket(conn, bucket):
    if not bucket:
        return
    if isinstance(bucket, str):
        try:
            data = json.loads(bucket)
        except Exception:
            data = {}
    elif isinstance(bucket, dict):
        data = bucket
    else:
        data = {}
    for name in data.keys():
        upsert_ingredient_name(conn, name)

def main():
    app = create_app()
    with app.app_context():
        with db.engine.begin() as conn:
            # 1) ensure the Tags catalog exists/seeded
            ensure_tags(conn)

            # 2) scan all meals and collect ingredient names into Ingredients catalog
            rows = conn.execute(text("SELECT Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients FROM MealsTable")).mappings().all()
            for r in rows:
                process_bucket(conn, r.get("Fresh_Ingredients"))
                process_bucket(conn, r.get("Tinned_Ingredients"))
                process_bucket(conn, r.get("Dry_Ingredients"))
                process_bucket(conn, r.get("Dairy_Ingredients"))

    print("✔ Catalogs refreshed: Ingredients, Tags.")

if __name__ == "__main__":
    main()
