from flask import Blueprint, render_template, request, redirect, url_for
import json
from ..utilities import parse_ingredients, execute_mysql_query
from ..variables import staples_list, book_list, fresh_ingredients, tinned_ingredients, dry_ingredients, dairy_ingredients

add = Blueprint('add', __name__, template_folder='templates', static_folder='../static')


@add.route('/add', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        details = request.form
        details_dict = details.to_dict()

        query = """
        INSERT INTO MealsTable
        (Name, Staple, Book, Page, Website,
         Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients)
        VALUES
        (:name, :staple, :book, :page, :website,
         :fresh_ing, :tinned_ing, :dry_ing, :dairy_ing)
        """

        params = {
            "name": details['Name'],
            "staple": details['Staple'],
            "book": details['Book'],
            "page": details['Page'],
            "website": details['Website'],
            "fresh_ing": parse_ingredients(details_dict, "Fresh ", remove_prefix=True),
            "tinned_ing": parse_ingredients(details_dict, "Tinned ", remove_prefix=True),
            "dry_ing": parse_ingredients(details_dict, "Dry ", remove_prefix=True),
            "dairy_ing": parse_ingredients(details_dict, "Dairy ", remove_prefix=True),
        }

        execute_mysql_query(query, params, fetch="none")

        return redirect(url_for('add.index'))

    return render_template(
        'add.html',
        len_staples=len(staples_list), staples=staples_list,
        len_books=len(book_list), books=book_list,
        len_fresh_ingredients=len(fresh_ingredients), fresh_ingredients=fresh_ingredients,
        len_tinned_ingredients=len(tinned_ingredients), tinned_ingredients=tinned_ingredients,
        len_dry_ingredients=len(dry_ingredients), dry_ingredients=dry_ingredients,
        len_dairy_ingredients=len(dairy_ingredients), dairy_ingredients=dairy_ingredients
    )
