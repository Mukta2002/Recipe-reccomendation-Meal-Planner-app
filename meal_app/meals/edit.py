from flask import Blueprint, render_template, request, redirect, url_for
import json
from ..utilities import execute_mysql_query, parse_ingredients, get_tag_keys, get_tags
from ..variables import staples_list, book_list, fresh_ingredients, tinned_ingredients, dry_ingredients, dairy_ingredients, tag_list

edit = Blueprint('edit', __name__, template_folder='templates', static_folder='../static')


@edit.route('/edit', methods=['GET', 'POST'])
def index():
    # Get all meal names
    query_string = "SELECT Name FROM MealsTable;"
    results = execute_mysql_query(query_string)
    meals = [result['Name'] for result in results]

    if request.method == "POST":
        details = request.form
        query_string = "SELECT * FROM MealsTable WHERE Name = :meal"
        results = execute_mysql_query(query_string, {"meal": details['Meal']}, fetch="all")
        return redirect(url_for('edit.edit_meal', meal=results[0]['Name']))

    return render_template('edit_list.html',
                           len_meals=len(meals), meals=meals)


@edit.route('/edit/<meal>', methods=['GET', 'POST'])
def edit_meal(meal):
    if request.method == "GET":
        query_string = "SELECT * FROM MealsTable WHERE Name = :meal"
        results = execute_mysql_query(query_string, {"meal": meal}, fetch="all")

        if not results:
            return f"No meal found with name {meal}", 404

        row = results[0]
        current_fresh_ingredients = json.loads(row['Fresh_Ingredients'])
        current_tinned_ingredients = json.loads(row['Tinned_Ingredients'])
        current_dry_ingredients = json.loads(row['Dry_Ingredients'])
        current_dairy_ingredients = json.loads(row['Dairy_Ingredients'])
        current_tags = [
            row['Spring_Summer'],
            row['Autumn_Winter'],
            row['Quick_Easy'],
            row['Special']
        ]

        return render_template(
            'edit_meal.html',
            meal_name=row['Name'], staple=row['Staple'],
            book=row['Book'], page=row['Page'], website=row['Website'],
            current_fresh_ingredients=current_fresh_ingredients,
            current_fresh_ingredients_keys=list(current_fresh_ingredients.keys()),
            current_tinned_ingredients=current_tinned_ingredients,
            current_tinned_ingredients_keys=list(current_tinned_ingredients.keys()),
            current_dry_ingredients=current_dry_ingredients,
            current_dry_ingredients_keys=list(current_dry_ingredients.keys()),
            current_dairy_ingredients=current_dairy_ingredients,
            current_dairy_ingredients_keys=list(current_dairy_ingredients.keys()),
            len_staples=len(staples_list), staples=staples_list,
            len_books=len(book_list), books=book_list,
            len_fresh_ingredients=len(fresh_ingredients),
            fresh_ingredients=[ingredient[0] for ingredient in fresh_ingredients],
            fresh_ingredients_units=[ingredient[1] for ingredient in fresh_ingredients],
            len_tinned_ingredients=len(tinned_ingredients),
            tinned_ingredients=[ingredient[0] for ingredient in tinned_ingredients],
            tinned_ingredients_units=[ingredient[1] for ingredient in tinned_ingredients],
            len_dry_ingredients=len(dry_ingredients),
            dry_ingredients=[ingredient[0] for ingredient in dry_ingredients],
            dry_ingredients_units=[ingredient[1] for ingredient in dry_ingredients],
            len_dairy_ingredients=len(dairy_ingredients),
            dairy_ingredients=[ingredient[0] for ingredient in dairy_ingredients],
            dairy_ingredients_units=[ingredient[1] for ingredient in dairy_ingredients],
            len_tags=len(tag_list), tags=tag_list,
            current_tags=current_tags
        )

    if request.method == "POST":
        details = request.form
        details_dict = details.to_dict()

        # parse ingredient groups
        fresh_ing = parse_ingredients(details_dict, "Fresh ")
        tinned_ing = parse_ingredients(details_dict, "Tinned ")
        dry_ing = parse_ingredients(details_dict, "Dry ")
        dairy_ing = parse_ingredients(details_dict, "Dairy ")

        # parse tags
        tag_values = []
        for key in list(details_dict.keys()):
            if 'Tag' in key:
                tag_values.append(details_dict[key])
        tags = get_tags(tag_values)

        # build update query safely
        query_string = """
        UPDATE MealsTable
        SET Name = :name,
            Staple = :staple,
            Book = :book,
            Page = :page,
            Website = :website,
            Fresh_Ingredients = :fresh_ing,
            Tinned_Ingredients = :tinned_ing,
            Dry_Ingredients = :dry_ing,
            Dairy_Ingredients = :dairy_ing,
            Spring_Summer = :spring,
            Autumn_Winter = :autumn,
            Quick_Easy = :quick,
            Special = :special
        WHERE Name = :meal
        """

        params = {
            "name": details['Name'],
            "staple": details['Staple'],
            "book": details['Book'],
            "page": details['Page'],
            "website": details['Website'],
            "fresh_ing": fresh_ing,
            "tinned_ing": tinned_ing,
            "dry_ing": dry_ing,
            "dairy_ing": dairy_ing,
            "spring": tags['Spring_Summer'],
            "autumn": tags['Autumn_Winter'],
            "quick": tags['Quick_Easy'],
            "special": tags['Special'],
            "meal": meal
        }

        execute_mysql_query(query_string, params, fetch="none")

        return redirect(url_for('edit.confirmation', meal=details['Name']))


@edit.route('/edit_confirmation/<meal>', methods=['GET', 'POST'])
def confirmation(meal):
    if request.method == "GET":
        query_string = "SELECT * FROM MealsTable WHERE Name = :meal"
        result = execute_mysql_query(query_string, {"meal": meal}, fetch="all")

        if not result:
            return f"No meal found with name {meal}", 404

        row = result[0]
        location_details = {}
        if row['Website'] is None or row['Website'] == '':
            location_details['Book'] = row['Book']
            location_details['Page'] = row['Page']
        else:
            location_details['Website'] = row['Website']

        fresh_ingredients = [list(json.loads(row['Fresh_Ingredients']).keys()),
                             list(json.loads(row['Fresh_Ingredients']).values())]
        tinned_ingredients = [list(json.loads(row['Tinned_Ingredients']).keys()),
                              list(json.loads(row['Tinned_Ingredients']).values())]
        dry_ingredients = [list(json.loads(row['Dry_Ingredients']).keys()),
                           list(json.loads(row['Dry_Ingredients']).values())]
        dairy_ingredients = [list(json.loads(row['Dairy_Ingredients']).keys()),
                             list(json.loads(row['Dairy_Ingredients']).values())]

        tags = [
            {"Spring/Summer": row['Spring_Summer']},
            {"Autumn/Winter": row['Autumn_Winter']},
            {"Quick/Easy": row['Quick_Easy']},
            {"Special": row['Special']}
        ]
        tags = get_tag_keys(tags)

        return render_template(
            'edit_confirmation.html',
            meal_name=meal,
            location_details=location_details, location_keys=location_details.keys(),
            staple=row['Staple'],
            len_fresh_ingredients=len(fresh_ingredients[0]), fresh_ingredients_keys=fresh_ingredients[0], fresh_ingredients_values=fresh_ingredients[1],
            len_tinned_ingredients=len(tinned_ingredients[0]), tinned_ingredients_keys=tinned_ingredients[0], tinned_ingredients_values=tinned_ingredients[1],
            len_dry_ingredients=len(dry_ingredients[0]), dry_ingredients_keys=dry_ingredients[0], dry_ingredients_values=dry_ingredients[1],
            len_dairy_ingredients=len(dairy_ingredients[0]), dairy_ingredients_keys=dairy_ingredients[0], dairy_ingredients_values=dairy_ingredients[1],
            len_tags=len(tags), tags=tags
        )
