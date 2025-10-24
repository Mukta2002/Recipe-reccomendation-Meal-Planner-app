-- initialise_db.sql  (3-table version)

-- MealsTable is created by database_setup/import_sample_data.py

-- 1) Ingredients catalogue
CREATE TABLE IF NOT EXISTS Ingredients (
  Ingredient_ID   INT AUTO_INCREMENT PRIMARY KEY,
  Ingredient_Name VARCHAR(150) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2) Tags catalogue (just the 4 you use)
CREATE TABLE IF NOT EXISTS Tags (
  Tag_ID   INT AUTO_INCREMENT PRIMARY KEY,
  Tag_Name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed the four flags as tags (idempotent)
INSERT IGNORE INTO Tags (Tag_Name)
VALUES ('Spring/Summer'), ('Autumn/Winter'), ('Quick/Easy'), ('Special');

-- If you had the junction tables before, drop them:
DROP TABLE IF EXISTS MealIngredients;
DROP TABLE IF EXISTS MealTags;
