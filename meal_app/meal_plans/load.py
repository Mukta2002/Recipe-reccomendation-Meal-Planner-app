from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from pathlib import Path
import json

load = Blueprint('load', __name__, template_folder='templates', static_folder='../static')

def candidate_dirs():
    """
    Return both possible save locations:
    1) <project_root>/saved_meal_plans
    2) <app_root>/saved_meal_plans  (meal_app/meal_app/saved_meal_plans)
    """
    app_root = Path(current_app.root_path)           # .../meal_app/meal_app
    project_root = app_root.parent                   # .../meal_app
    return [
        project_root / "saved_meal_plans",
        app_root / "saved_meal_plans",
    ]

def list_saved_plans():
    """
    Find saved plans in either directory.
    Accept files with or without .json (to tolerate old Windows-incompatible names).
    Return a sorted list of display names (without extension).
    """
    names = set()
    for d in candidate_dirs():
        if not d.exists():
            continue
        # *.json files
        for p in d.glob("*.json"):
            names.add(p.stem)
        # files without extension (to tolerate earlier ':' issue)
        for p in d.glob("*"):
            if p.is_file() and p.suffix == "":
                names.add(p.name)  # keep raw name; we'll try to open with and without .json
    return sorted(names)

def resolve_plan_path(meal_plan: str) -> Path | None:
    """
    Try to resolve a saved plan filename across both locations,
    trying these forms:
      - <name>.json
      - <name>      (no extension)
    Return the first that exists, else None.
    """
    for d in candidate_dirs():
        cand_json = d / f"{meal_plan}.json"
        if cand_json.exists():
            return cand_json
        cand_raw = d / meal_plan
        if cand_raw.exists():
            return cand_raw
    return None

@load.route('/load', methods=['GET', 'POST'])
def choose_meal_plan():
    meal_plans = list_saved_plans()

    if not meal_plans:
        return render_template('no_meal_plans.html')

    if request.method == "POST":
        selected = request.form.get('Meal Plan') or request.form.get('Meal_Plan')
        if not selected:
            return redirect(url_for('load.choose_meal_plan'))
        return redirect(url_for('load.load_meal_plan', meal_plan=selected))

    return render_template('load.html', len_meal_plans=len(meal_plans), meal_plans=meal_plans)

@load.route('/load/<meal_plan>', methods=['GET', 'POST'])
def load_meal_plan(meal_plan):
    plan_path = resolve_plan_path(meal_plan)
    if not plan_path:
        # Not found anywhere; back to chooser
        return redirect(url_for('load.choose_meal_plan'))

    with plan_path.open("r", encoding="utf-8") as f:
        session['complete_ingredient_dict'] = json.load(f)

    return redirect(url_for('display.display_meal_plan'))
