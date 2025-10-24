from flask import Blueprint, render_template, request, redirect, url_for
import json
from ..utilities import execute_mysql_query

find = Blueprint('find', __name__, template_folder='templates', static_folder='../static')


@find.route('/find', methods=['GET', 'POST'])
def index():
    # Get all meal names
    query_string = "SELECT Name FROM MealsTable;"
    results = execute_mysql_query(query_string)
    meals = [result['Name'] for result in results]

    if request.method == "POST":
        details = request.form
        query_string = "SELECT * FROM MealsTable WHERE Name = :meal"
        results = execute_mysql_query(query_string, {"meal": details['Meal']}, fetch="all")
        return redirect(url_for('find.some_meal_page', meal=results[0]['Name']))

    return render_template(
        'find.html',
        len_meals=len(meals),
        meals=meals
    )


@find.route('/find/<meal>', methods=['GET', 'POST'])
def some_meal_page(meal):
    if request.method == "GET":
        query = "SELECT * FROM MealsTable WHERE Name = :meal"
        result = execute_mysql_query(query, {"meal": meal}, fetch="all")

        if not result:
            return f"No meal found with name {meal}", 404

        row = result[0]

        # build location details
        location_details = {}
        if row.get('Website') is None or row.get('Website') == '':
            location_details['Book'] = row.get('Book')
            location_details['Page'] = row.get('Page')
        else:
            location_details['Website'] = row.get('Website')

        # parse ingredients
        fresh_ingredients = [
            list(json.loads(row['Fresh_Ingredients']).keys()),
            list(json.loads(row['Fresh_Ingredients']).values())
        ]
        tinned_ingredients = [
            list(json.loads(row['Tinned_Ingredients']).keys()),
            list(json.loads(row['Tinned_Ingredients']).values())
        ]
        dry_ingredients = [
            list(json.loads(row['Dry_Ingredients']).keys()),
            list(json.loads(row['Dry_Ingredients']).values())
        ]
        dairy_ingredients = [
            list(json.loads(row['Dairy_Ingredients']).keys()),
            list(json.loads(row['Dairy_Ingredients']).values())
        ]

        return render_template(
            'find_results.html',
            meal_name=meal,
            location_details=location_details, location_keys=location_details.keys(),
            staple=row.get('Staple'),
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
            dairy_ingredients_values=dairy_ingredients[1]
        )
    else:
        return redirect(url_for('find.index'))
