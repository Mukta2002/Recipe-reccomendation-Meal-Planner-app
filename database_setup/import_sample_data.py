# database_setup/import_sample_data.py
"""
Imports sample data into the MealsTable using your Flask/SQLAlchemy config.
- Creates MealsTable if it doesn't exist
- Loads database_setup/sample_database_data.json
- Inserts/updates rows idempotently (safe to run multiple times)
"""

import json
from pathlib import Path
from sqlalchemy import text
from meal_app import create_app, db  # uses your app's config/DB URI


# Path to the JSON shipped in the repo
JSON_PATH = Path(__file__).resolve().parent / "sample_database_data.json"

# SQL to create the table expected by the app
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS MealsTable (
  Meal_ID INT AUTO_INCREMENT PRIMARY KEY,
  Name VARCHAR(255) NOT NULL,
  Staple VARCHAR(100),
  Book VARCHAR(100),
  Page VARCHAR(10),
  Website VARCHAR(255),
  Fresh_Ingredients JSON NULL,
  Tinned_Ingredients JSON NULL,
  Dry_Ingredients JSON NULL,
  Dairy_Ingredients JSON NULL,
  Last_Made DATE NULL,
  Spring_Summer TINYINT(1) NOT NULL DEFAULT 0,
  Autumn_Winter TINYINT(1) NOT NULL DEFAULT 0,
  Quick_Easy   TINYINT(1) NOT NULL DEFAULT 0,
  Special      TINYINT(1) NOT NULL DEFAULT 0,
  UNIQUE KEY uk_meal_name (Name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Parameterized insert with upsert behavior
INSERT_SQL = text("""
INSERT INTO MealsTable
  (Name, Staple, Book, Page, Website,
   Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients,
   Last_Made, Spring_Summer, Autumn_Winter, Quick_Easy, Special)
VALUES
  (:Name, :Staple, :Book, :Page, :Website,
   :Fresh_Ingredients, :Tinned_Ingredients, :Dry_Ingredients, :Dairy_Ingredients,
   NULL, 0, 0, 0, 0)
ON DUPLICATE KEY UPDATE
  Staple=VALUES(Staple),
  Book=VALUES(Book),
  Page=VALUES(Page),
  Website=VALUES(Website),
  Fresh_Ingredients=VALUES(Fresh_Ingredients),
  Tinned_Ingredients=VALUES(Tinned_Ingredients),
  Dry_Ingredients=VALUES(Dry_Ingredients),
  Dairy_Ingredients=VALUES(Dairy_Ingredients);
""")


def main():
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"Could not find JSON file at: {JSON_PATH}")

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    app = create_app()
    with app.app_context():
        # Ensure table exists
        with db.engine.begin() as conn:
            conn.execute(text(CREATE_TABLE_SQL))

        # Insert/update rows
        with db.engine.begin() as conn:
            for row in data:
                params = {
                    "Name": row.get("Name", ""),
                    "Staple": row.get("Staple", ""),
                    "Book": row.get("Book", ""),
                    "Page": row.get("Page", ""),
                    "Website": row.get("Website", ""),
                    # JSON columns must be JSON strings
                    "Fresh_Ingredients": json.dumps(row.get("Fresh_Ingredients", {})),
                    "Tinned_Ingredients": json.dumps(row.get("Tinned_Ingredients", {})),
                    "Dry_Ingredients": json.dumps(row.get("Dry_Ingredients", {})),
                    "Dairy_Ingredients": json.dumps(row.get("Dairy_Ingredients", {})),
                }
                conn.execute(INSERT_SQL, params)
            

    print("✔ Imported sample data into MealsTable.")


if __name__ == "__main__":
    main()

