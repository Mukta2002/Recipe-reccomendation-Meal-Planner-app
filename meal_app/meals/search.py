from flask import Blueprint, render_template, request, redirect, url_for, session
import json
from ..utilities import execute_mysql_query

search = Blueprint('search', __name__, template_folder='templates', static_folder='../static')


@search.route('/search', methods=['GET', 'POST'])
def index():
    # Get all ingredient JSONs to build dropdown lists
    query_string = """
    SELECT Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients
    FROM MealsTable
    WHERE JSON_LENGTH(Fresh_Ingredients) > 0;
    """
    results = execute_mysql_query(query_string, fetch="all")

    # collect unique keys for each ingredient category
    fresh_ingredients = sorted({key for r in results for key in json.loads(r['Fresh_Ingredients']).keys()})
    tinned_ingredients = sorted({key for r in results for key in json.loads(r['Tinned_Ingredients']).keys()})
    dry_ingredients = sorted({key for r in results for key in json.loads(r['Dry_Ingredients']).keys()})
    dairy_ingredients = sorted({key for r in results for key in json.loads(r['Dairy_Ingredients']).keys()})

    if request.method == "POST":
        details_dict = request.form.to_dict()

        ingredient = None
        json_key = None

        if "null" not in details_dict.get("Fresh_Ingredients", "null"):
            json_key = "Fresh_Ingredients"
            ingredient = details_dict[json_key]
        elif "null" not in details_dict.get("Tinned_Ingredients", "null"):
            json_key = "Tinned_Ingredients"
            ingredient = details_dict[json_key]
        elif "null" not in details_dict.get("Dry_Ingredients", "null"):
            json_key = "Dry_Ingredients"
            ingredient = details_dict[json_key]
        elif "null" not in details_dict.get("Dairy_Ingredients", "null"):
            json_key = "Dairy_Ingredients"
            ingredient = details_dict[json_key]

        if ingredient and json_key:
            # Note: ingredient name is inserted into JSON path string
            # It's safe because it comes from dropdown lists we control
            query = f"""
            SELECT *
            FROM MealsTable
            WHERE JSON_EXTRACT({json_key}, '$."{ingredient}"') IS NOT NULL;
            """
            results = execute_mysql_query(query, fetch="all")
            session['meal_list'] = [row['Name'] for row in results]

            return redirect(url_for('search.search_results', ingredient=ingredient))

    return render_template(
        'search.html',
        len_fresh_ingredients=len(fresh_ingredients), fresh_ingredients=fresh_ingredients,
        len_tinned_ingredients=len(tinned_ingredients), tinned_ingredients=tinned_ingredients,
        len_dry_ingredients=len(dry_ingredients), dry_ingredients=dry_ingredients,
        len_dairy_ingredients=len(dairy_ingredients), dairy_ingredients=dairy_ingredients
    )


@search.route('/search/<ingredient>', methods=['GET', 'POST'])
def search_results(ingredient):
    if request.method == "GET":
        meals = session.pop('meal_list', [])
        return render_template(
            'search_results.html',
            ingredient=ingredient,
            len_meals=len(meals),
            meals=meals
        )
    else:
        return redirect(url_for('search.index'))
