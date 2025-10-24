from flask import Blueprint, render_template, request, redirect, url_for
from pathlib import Path

delete = Blueprint('delete', __name__, template_folder='templates', static_folder='../static')

# Match where your app actually saves plans (working dir / saved_meal_plans)
SAVED_DIR = Path.cwd() / "saved_meal_plans"


def _valid_json_file(p: Path) -> bool:
    """Return True if p exists, is a non-empty file, and likely JSON."""
    try:
        if not p.is_file() or p.stat().st_size == 0:
            return False
        with p.open("r", encoding="utf-8", errors="ignore") as f:
            first = f.read(1).strip()
        return first in ("{", "[")
    except Exception:
        return False


def _list_saved_names() -> list[str]:
    """Return plan names (no extension) for all usable files."""
    names = set()
    if SAVED_DIR.exists():
        # *.json files
        for p in SAVED_DIR.glob("*.json"):
            if _valid_json_file(p):
                names.add(p.stem)
        # files without extension (just in case)
        for p in SAVED_DIR.glob("*"):
            if p.suffix == "" and _valid_json_file(p):
                names.add(p.name)
    return sorted(names)


def _resolve_plan_path(name: str) -> Path | None:
    """Find the actual file for a given plan name, trying safe variants."""
    candidates: list[Path] = [
        SAVED_DIR / f"{name}.json",
        SAVED_DIR / name,
    ]
    # Handle Windows-unsafe characters like ":" that might have been replaced
    safe1 = name.replace(":", "-")
    safe2 = name.replace(":", "_")
    if safe1 != name:
        candidates += [SAVED_DIR / f"{safe1}.json", SAVED_DIR / safe1]
    if safe2 != name:
        candidates += [SAVED_DIR / f"{safe2}.json", SAVED_DIR / safe2]

    for p in candidates:
        if p.exists():
            return p
    return None


def delete_plans(meal_plan_list: list[str]) -> None:
    """Delete the selected meal plan files (any of the name variants)."""
    for name in meal_plan_list:
        path = _resolve_plan_path(name)
        if path:
            # Path.unlink supports missing_ok=True on Py3.8+; safe in your 3.11 env
            path.unlink(missing_ok=True)


@delete.route('/delete', methods=['GET', 'POST'])
def delete_meal_plan():
    SAVED_DIR.mkdir(parents=True, exist_ok=True)
    meal_plans = _list_saved_names()

    if not meal_plans:
        return render_template('no_meal_plans.html')

    if request.method == "POST":
        # Collect all checkbox values. Templates often use keys like:
        # "Meal Plan 1", "Meal Plan 2" (or "Meal_Plan_*")
        selected = [v for k, v in request.form.items() if ('Meal Plan' in k) or ('Meal_Plan' in k)]
        if not selected:
            # Nothing selected; reload the page
            return redirect(url_for('delete.delete_meal_plan'))

        delete_plans(selected)
        return render_template('delete_complete.html')

    return render_template('delete.html', meal_plans=meal_plans)
