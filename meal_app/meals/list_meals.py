from flask import Blueprint, render_template, request, redirect, url_for
import json
from datetime import datetime
from ..utilities import execute_mysql_query

list_meals = Blueprint('list_meals', __name__, template_folder='templates', static_folder='../static')


@list_meals.route('/list_meals', methods=['GET', 'POST'])
def index():
    if request.method == "GET":
        # Order by Book then Page (numeric)
        query_string = """
        SELECT *, CAST(Page AS SIGNED) AS Page
        FROM MealsTable
        ORDER BY Book, Page;
        """
        results = execute_mysql_query(query_string, fetch="all")

        meal_names = [meal['Name'] for meal in results]
        staples = [meal['Staple'] for meal in results]
        books = [meal['Book'] for meal in results]
        pages = [meal['Page'] for meal in results]
        websites = [meal['Website'] for meal in results]
        last_dates = [
            datetime.strftime(meal['Last_Made'], "%d-%m-%Y")
            if meal['Last_Made'] else ""
            for meal in results
        ]

        return render_template(
            'list_meals.html',
            len_meals=len(meal_names),
            meal_names=meal_names,
            staples=staples,
            books=books,
            page=pages,
            website=websites,
            last_date=last_dates
        )

    elif request.method == "POST" and request.form.get('submit'):
        # Get selected meal name
        details_dict = request.form.to_dict()
        meal = details_dict['submit']
        return redirect(url_for('find.some_meal_page', meal=meal))
