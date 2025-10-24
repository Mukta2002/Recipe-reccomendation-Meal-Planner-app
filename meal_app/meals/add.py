from flask import Blueprint, render_template, request, redirect, url_for
import json
from ..utilities import execute_mysql_query, parse_ingredients, get_tag_keys, get_tags
from ..variables import staples_list, book_list, fresh_ingredients, tinned_ingredients, dry_ingredients, dairy_ingredients, tag_list

add = Blueprint('add', __name__, template_folder='templates', static_folder='../static')


@add.route('/add', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        details = request.form
        details_dict = details.to_dict()

        # collect tags from form
        tag_values = []
        for key in list(details_dict.keys()):
            if 'Tag' in key:
                tag_values.append(details_dict[key])

        tags = get_tags(tag_values)

        # build query with placeholders to avoid SQL injection
        query = """
        INSERT INTO MealsTable
        (Name, Staple, Book, Page, Website,
         Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients,
         Last_Made, Spring_Summer, Autumn_Winter, Quick_Easy, Special)
        VALUES
        (:name, :staple, :book, :page, :website,
         :fresh_ing, :tinned_ing, :dry_ing, :dairy_ing,
         :last_made, :spring, :autumn, :quick, :special)
        """

        params = {
            "name": details["Name"],
            "staple": details["Staple"],
            "book": details["Book"],
            "page": details["Page"],
            "website": details["Website"],
            "fresh_ing": parse_ingredients(details_dict, "Fresh "),
            "tinned_ing": parse_ingredients(details_dict, "Tinned "),
            "dry_ing": parse_ingredients(details_dict, "Dry "),
            "dairy_ing": parse_ingredients(details_dict, "Dairy "),
            "last_made": "2021-01-01",  # static for now
            "spring": tags["Spring_Summer"],
            "autumn": tags["Autumn_Winter"],
            "quick": tags["Quick_Easy"],
            "special": tags["Special"],
        }

        # run query (no fetch because it's an INSERT)
        execute_mysql_query(query, params, fetch="none")

        return redirect(url_for('add.confirmation', meal=details['Name']))

    return render_template(
        'add.html',
        len_staples=len(staples_list), staples=staples_list,
        len_books=len(book_list), books=book_list,
        len_fresh_ingredients=len(fresh_ingredients), fresh_ingredients=[ingredient[0] for ingredient in fresh_ingredients],
        fresh_ingredients_units=[ingredient[1] for ingredient in fresh_ingredients],
        len_tinned_ingredients=len(tinned_ingredients), tinned_ingredients=[ingredient[0] for ingredient in tinned_ingredients],
        tinned_ingredients_units=[ingredient[1] for ingredient in tinned_ingredients],
        len_dry_ingredients=len(dry_ingredients), dry_ingredients=[ingredient[0] for ingredient in dry_ingredients],
        dry_ingredients_units=[ingredient[1] for ingredient in dry_ingredients],
        len_dairy_ingredients=len(dairy_ingredients), dairy_ingredients=[ingredient[0] for ingredient in dairy_ingredients],
        dairy_ingredients_units=[ingredient[1] for ingredient in dairy_ingredients],
        len_tags=len(tag_list), tags=tag_list
    )


@add.route('/add_confirmation/<meal>', methods=['GET', 'POST'])
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
            'add_confirmation.html',
            meal_name=meal,
            location_details=location_details, location_keys=location_details.keys(),
            staple=row['Staple'],
            len_fresh_ingredients=len(fresh_ingredients[0]), fresh_ingredients_keys=fresh_ingredients[0], fresh_ingredients_values=fresh_ingredients[1],
            len_tinned_ingredients=len(tinned_ingredients[0]), tinned_ingredients_keys=tinned_ingredients[0], tinned_ingredients_values=tinned_ingredients[1],
            len_dry_ingredients=len(dry_ingredients[0]), dry_ingredients_keys=dry_ingredients[0], dry_ingredients_values=dry_ingredients[1],
            len_dairy_ingredients=len(dairy_ingredients[0]), dairy_ingredients_keys=dairy_ingredients[0], dairy_ingredients_values=dairy_ingredients[1],
            len_tags=len(tags), tags=tags
        )
