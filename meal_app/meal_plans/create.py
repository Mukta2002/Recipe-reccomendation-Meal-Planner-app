from flask import Blueprint, render_template, request, redirect, url_for, session
import json
from ..utilities import execute_mysql_query
from ..variables import extras

create = Blueprint('create', __name__, template_folder='templates', static_folder='../static')


def get_meal_info(meal_list, quantity_list) -> list[dict]:
    """
    Fetch JSON ingredients for each meal and attach its requested quantity.
    Returns a list of dicts like:
    {
      'Fresh_Ingredients': {...} | {},
      'Tinned_Ingredients': {...} | {},
      'Dry_Ingredients': {...} | {},
      'Dairy_Ingredients': {...} | {},
      'quantity': N
    }
    """
    results = []
    q = """
      SELECT Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients
      FROM MealsTable
      WHERE Name = :name
    """
    for idx, meal in enumerate(meal_list):
        row = execute_mysql_query(q, {"name": meal}, fetch="one")
        if not row:
            # Skip unknown meal names gracefully
            continue

        # Safely parse JSON (handle NULLs)
        def _loads(v):
            if v in (None, "", "null"):
                return {}
            return json.loads(v)

        parsed = {
            "Fresh_Ingredients": _loads(row.get("Fresh_Ingredients")),
            "Tinned_Ingredients": _loads(row.get("Tinned_Ingredients")),
            "Dry_Ingredients": _loads(row.get("Dry_Ingredients")),
            "Dairy_Ingredients": _loads(row.get("Dairy_Ingredients")),
            "quantity": quantity_list[idx],
        }
        results.append(parsed)
    return results


def quantity_adjustment(meal_list_dict) -> list[dict]:
    """Multiply each ingredient quantity by the meal's selected quantity."""
    def _scale(dct, factor):
        if not isinstance(dct, dict):
            return {}
        for k, v in list(dct.items()):
            try:
                dct[k] = float(v) * float(factor)
            except (TypeError, ValueError):
                # If a value is non-numeric, drop it to avoid crashes
                dct.pop(k, None)
        return dct

    for meal in meal_list_dict:
        qty = meal.get("quantity", 1) or 1
        meal["Fresh_Ingredients"] = _scale(meal.get("Fresh_Ingredients", {}), qty)
        meal["Tinned_Ingredients"] = _scale(meal.get("Tinned_Ingredients", {}), qty)
        meal["Dry_Ingredients"] = _scale(meal.get("Dry_Ingredients", {}), qty)
        meal["Dairy_Ingredients"] = _scale(meal.get("Dairy_Ingredients", {}), qty)
        meal.pop("quantity", None)
    return meal_list_dict


def build_ingredient_dictionary(meal_ingredient_dict, complete_ingredient_dict, ingredient_type) -> dict:
    """
    Add quantities for a single ingredient type (e.g., 'Fresh_Ingredients')
    into the combined totals dict.
    """
    for ingredient, val in meal_ingredient_dict.items():
        try:
            val = float(val)
        except (TypeError, ValueError):
            continue

        bucket = complete_ingredient_dict[ingredient_type]
        bucket[ingredient] = bucket.get(ingredient, 0) + val

        # Normalize numbers (e.g., 2.0 -> 2)
        bucket[ingredient] = round(bucket[ingredient], 2)
        if float(bucket[ingredient]).is_integer():
            bucket[ingredient] = int(bucket[ingredient])
    return complete_ingredient_dict


def collate_ingredients(meal_info_list) -> dict:
    """Combine all meals' ingredients into one deduped dictionary."""
    if not meal_info_list:
        return {
            "Fresh_Ingredients": {},
            "Tinned_Ingredients": {},
            "Dry_Ingredients": {},
            "Dairy_Ingredients": {},
        }

    # Ensure all expected keys exist
    complete_ingredient_dict = {
        "Fresh_Ingredients": {},
        "Tinned_Ingredients": {},
        "Dry_Ingredients": {},
        "Dairy_Ingredients": {},
    }

    for meal in meal_info_list:
        for ingredient_type in complete_ingredient_dict.keys():
            dct = meal.get(ingredient_type) or {}
            if dct:
                build_ingredient_dictionary(dct, complete_ingredient_dict, ingredient_type)

    return complete_ingredient_dict

@create.route('/create', methods=['GET', 'POST'])
def create_meal_plan():
    # Pull meals grouped by staple (no schema prefix; use current DB)
    query_string = """
      SELECT GROUP_CONCAT(Name ORDER BY Name ASC) AS Meals, Staple
      FROM MealsTable
      GROUP BY Staple;
    """
    results = execute_mysql_query(query_string, fetch="all") or []

    # Build dict: {staple: [meal names...]}
    staples_dict = {}
    for item in results:
        staple = str(item.get('Staple') or '')
        meals_csv = item.get('Meals') or ''
        meals_list = [m for m in meals_csv.split(',') if m] if meals_csv else []
        staples_dict[staple] = meals_list

    if request.method == "POST":
        details = request.form.to_dict()

        # Helper: extract a sortable index from a key (e.g., "Meal 2", "Meal_10", "Quantity3")
        import re
        def key_index(k: str) -> tuple:
            # find first number in key; if none, return a big index so it sorts last
            m = re.search(r'(\d+)', k)
            return (int(m.group(1)) if m else 10**9, k.lower())

        # Collect meals by *any* field containing "Meal"
        meal_keys = sorted([k for k in details if 'meal' in k.lower()], key=key_index)
        meals_raw = [details[k].strip() for k in meal_keys if details[k] and details[k].strip().lower() != 'null']

        # Collect quantities by *any* field containing "Quantity"
        qty_keys = sorted([k for k in details if 'quantity' in k.lower()], key=key_index)
        qty_raw = []
        for k in qty_keys:
            v = details.get(k, '1').strip()
            try:
                qty_raw.append(int(v))
            except ValueError:
                qty_raw.append(1)

        # Align lengths
        meal_list = meals_raw
        if len(qty_raw) < len(meal_list):
            qty_raw += [1] * (len(meal_list) - len(qty_raw))
        quantity_list = qty_raw[:len(meal_list)]

        # If nothing selected, just re-render the page (no redirect loop)
        if not meal_list:
            return render_template('create.html', staples_dict=staples_dict, extras=extras)

        # Build the final ingredient set
        meal_info = get_meal_info(meal_list, quantity_list)
        adjusted  = quantity_adjustment(meal_info)
        complete_ingredient_dict = collate_ingredients(adjusted)

        # Extras selected by user (checkboxes like Extra 1 / Extra_1, etc.)
        extras_selected = []
        for k, v in details.items():
            if 'extra' in k.lower() and v and v.strip().lower() != 'null':
                extras_selected.append(v.strip())

        complete_ingredient_dict['Extra_Ingredients'] = extras_selected
        complete_ingredient_dict['Meal_List'] = meal_list

        session['complete_ingredient_dict'] = complete_ingredient_dict
        return redirect(url_for('display.display_meal_plan'))

    return render_template('create.html', staples_dict=staples_dict, extras=extras)
