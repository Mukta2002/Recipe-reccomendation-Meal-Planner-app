"""
DEPRECATED.

The application stores ingredients inside JSON columns on MealsTable
(Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients).

Use:
  - database_setup/import_sample_data.py   -> creates MealsTable and loads sample_database_data.json
  - database_setup/add_dates.py            -> optional helper to backfill Last_Made

This file is intentionally disabled to avoid creating an unused `Ingredients` table.
"""
if __name__ == "__main__":
    print("This script is deprecated. Use import_sample_data.py instead.")
