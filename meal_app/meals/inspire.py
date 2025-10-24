from flask import Blueprint, render_template, request
import json
from datetime import datetime
from ..utilities import execute_mysql_query
from ..variables import tag_list

inspire = Blueprint('inspire', __name__, template_folder='templates', static_folder='../static')


@inspire.route('/inspire', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        details = request.form
        # Replace "/" with "_" to match DB column name
        tag = details['Tag'].replace('/', '_')

        # Build query: safe because `tag` comes only from predefined tag_list
        query_string = f"""
        SELECT Name, Staple, Last_Made
        FROM MealsTable
        WHERE {tag} = 1
        ORDER BY Name;
        """

        results = execute_mysql_query(query_string, fetch="all")

        meal_names = [meal['Name'] for meal in results]
        staples = [meal['Staple'] for meal in results]
        last_date = [
            datetime.strftime(meal['Last_Made'], "%d-%m-%Y")
            if meal['Last_Made'] else ""
            for meal in results
        ]

        return render_template(
            'inspire_results.html',
            tag=details['Tag'],
            len_meals=len(meal_names),
            meal_names=meal_names,
            staples=staples,
            last_date=last_date
        )

    return render_template(
        'inspire.html',
        len_tags=len(tag_list),
        tags=tag_list
    )
