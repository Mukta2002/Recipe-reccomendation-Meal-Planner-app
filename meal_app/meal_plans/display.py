from flask import Blueprint, redirect, url_for, render_template, request, session
import os
import json
from datetime import datetime
from ..utilities import execute_mysql_query

display = Blueprint('display', __name__, template_folder='templates', static_folder='../static')


def save_meal_plan(complete_ingredient_dict):
    """Saves created meal plan to the local saved_meal_plans directory."""
    if not os.path.exists('saved_meal_plans'):
        os.makedirs('saved_meal_plans')
    dt_string = datetime.now().strftime("%Y-%m-%d %H:%M")
    json_file = json.dumps(complete_ingredient_dict, indent=4)
    with open(f"saved_meal_plans/{dt_string}.json", "w", encoding="utf-8") as f:
        f.write(json_file)
    file_path = str(os.getcwd()) + f"/saved_meal_plans/{dt_string}.json"
    return file_path


def create_meal_info_table(rows):
    """Creates a nested list of meal information for rendering in display.html."""
    meal_info_list = []
    for meal in rows:
        name = meal.get('Name', '')
        website = meal.get('Website') or ''
        book = meal.get('Book') or ''
        page = meal.get('Page') or ''
        meal_info_list.append(
            [name, website] if website else [name, f"{book}, page {page}"]
        )
    return meal_info_list


def append_ingredient_units(fresh_ingredients, tinned_ingredients, dry_ingredients, dairy_ingredients):
    """Appends unit suffixes to ingredient quantities where appropriate."""
    from ..variables import gram_list
    # fresh
    fresh_ingredients[1] = [
        f"{fresh_ingredients[1][idx]} g" if fresh_ingredients[0][idx] in gram_list else str(fresh_ingredients[1][idx])
        for idx, _ in enumerate(fresh_ingredients[1])
    ]
    # tinned
    def _tinned_unit(val, name):
        if name in gram_list:
            return f"{val} g"
        try:
            num = float(val)
        except (TypeError, ValueError):
            return str(val)
        if num <= 1:
            return f"{int(num) if num.is_integer() else num} tin"
        return f"{int(num) if num.is_integer() else num} tins"

    tinned_ingredients[1] = [
        _tinned_unit(tinned_ingredients[1][idx], tinned_ingredients[0][idx])
        for idx, _ in enumerate(tinned_ingredients[1])
    ]
    # dry
    dry_ingredients[1] = [
        f"{dry_ingredients[1][idx]} g" if dry_ingredients[0][idx] in gram_list else str(dry_ingredients[1][idx])
        for idx, _ in enumerate(dry_ingredients[1])
    ]
    # dairy
    dairy_ingredients[1] = [
        (f"{dairy_ingredients[1][idx]} g" if dairy_ingredients[0][idx] in gram_list
         else f"{dairy_ingredients[1][idx]} ml" if str(dairy_ingredients[0][idx]) == 'Milk'
         else str(dairy_ingredients[1][idx]))
        for idx, _ in enumerate(dairy_ingredients[1])
    ]
    return fresh_ingredients, tinned_ingredients, dry_ingredients, dairy_ingredients


@display.route('/display', methods=['GET', 'POST'])
def display_meal_plan():
    if request.method == "GET":
        # Pull data from session
        complete_ingredient_dict = session.pop('complete_ingredient_dict', None)
        if not complete_ingredient_dict:
            return redirect(url_for('create.create_meal_plan'))
        session['complete_ingredient_dict'] = complete_ingredient_dict

        meal_list = complete_ingredient_dict.get('Meal_List', []) or []
        if not meal_list:
            # No meals selected -> go back to Create page
            return redirect(url_for('create.create_meal_plan'))

        # Build a safe parameterized IN clause ( :n0, :n1, ... )
        placeholders = ", ".join([f":n{i}" for i in range(len(meal_list))])
        params = {f"n{i}": name for i, name in enumerate(meal_list)}

        query_string = f"""
            SELECT Name, Book, Page, Website
            FROM MealsTable
            WHERE Name IN ({placeholders});
        """
        results = execute_mysql_query(query_string, params, fetch="all") or []
        info_meal_list = create_meal_info_table(results)

        # Prepare ingredient lists for rendering
        fresh_ingredients = [
            list(complete_ingredient_dict.get("Fresh_Ingredients", {}).keys()),
            list(complete_ingredient_dict.get("Fresh_Ingredients", {}).values()),
        ]
        tinned_ingredients = [
            list(complete_ingredient_dict.get("Tinned_Ingredients", {}).keys()),
            list(complete_ingredient_dict.get("Tinned_Ingredients", {}).values()),
        ]
        dry_ingredients = [
            list(complete_ingredient_dict.get("Dry_Ingredients", {}).keys()),
            list(complete_ingredient_dict.get("Dry_Ingredients", {}).values()),
        ]
        dairy_ingredients = [
            list(complete_ingredient_dict.get("Dairy_Ingredients", {}).keys()),
            list(complete_ingredient_dict.get("Dairy_Ingredients", {}).values()),
        ]
        fresh_ingredients, tinned_ingredients, dry_ingredients, dairy_ingredients = append_ingredient_units(
            fresh_ingredients, tinned_ingredients, dry_ingredients, dairy_ingredients
        )

        return render_template(
            'display.html',
            len_meal_info_list=len(info_meal_list),
            meal_info_list=info_meal_list,
            len_fresh_ingredients=len(fresh_ingredients[0]),
            fresh_ingredients_keys=fresh_ingredients[0],
            fresh_ingredients_values=fresh_ingredients[1],
            len_tinned_ingredients=len(tinned_ingredients[0]),
            tinned_ingredients_keys=tinned_ingredients[0],
            tinned_ingredients_values=tinned_ingredients[1],
            len_dry_ingredients=len(dry_ingredients[0]),
            dry_ingredients_keys=dry_ingredients[0],
            dry_ingredients_values=dry_ingredients[1],
            len_dairy_ingredients=len(dairy_ingredients[0]),
            dairy_ingredients_keys=dairy_ingredients[0],
            dairy_ingredients_values=dairy_ingredients[1],
            len_extra_ingredients=len(complete_ingredient_dict.get('Extra_Ingredients', [])),
            extra_ingredients=complete_ingredient_dict.get('Extra_Ingredients', []),
        )

    # POST
    complete_ingredient_dict = session.pop('complete_ingredient_dict', None)
    if not complete_ingredient_dict:
        return redirect(url_for('create.create_meal_plan'))
    session['complete_ingredient_dict'] = complete_ingredient_dict

    submit_val = request.form.get('submit', '')
    if submit_val == 'Save':
        file_path = save_meal_plan(complete_ingredient_dict)
        return render_template('save_complete.html', file_path=file_path)

    if submit_val == 'Update Dates':
        # Windows-safe date format (no %-m)
        date_now = datetime.now().strftime("%Y-%m-%d")
        meals = complete_ingredient_dict.get('Meal_List', [])
        if meals:
            for name in meals:
                execute_mysql_query(
                    "UPDATE MealsTable SET Last_Made = :dt WHERE Name = :name",
                    {"dt": date_now, "name": name},
                    fetch="none",
                )
        return redirect(url_for('display.display_meal_plan'))

    # Fallback: go back if unknown submit action
    return redirect(url_for('create.create_meal_plan'))
