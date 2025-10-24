import json
from sqlalchemy import text
from . import db


from sqlalchemy import text
from . import db

def execute_mysql_query(query_string, params=None, fetch="all"):
    """
    Runs a SQL statement using SQLAlchemy's engine.

    - query_string: SQL with optional :named params
    - params: dict of parameters
    - fetch: "all" (default), "one", or "none" (for INSERT/UPDATE/DELETE)

    Returns:
      - list[dict] for "all"
      - dict or None for "one"
      - None for "none" or non-SELECT
    """
    params = params or {}
    if fetch not in ("all", "one", "none"):
        fetch = "all"

    with db.engine.begin() as conn:
        result = conn.execute(text(query_string), params)

        # Non-SELECT (no rows) → nothing to fetch
        try:
            returns_rows = result.returns_rows  # SA 1.4+/2.0
        except AttributeError:
            # SA 1.3 doesn't expose returns_rows; infer from cursor
            returns_rows = hasattr(result, "cursor") and getattr(result.cursor, "description", None)

        if not returns_rows:
            return None

        # Try SA 1.4+/2.0 path first
        try:
            mappings = result.mappings()
            if fetch == "one":
                row = mappings.first()
                return row if row is not None else None
            else:
                return list(mappings.all())
        except AttributeError:
            # SA 1.3 fallback: build dicts from rows + keys
            rows = result.fetchall()
            keys = result.keys()
            dict_rows = [dict(zip(keys, row)) for row in rows]

            if fetch == "one":
                return dict_rows[0] if dict_rows else None
            else:
                return dict_rows



def parse_ingredients(ingredients_dict, filter_word, remove_prefix=False):
    """
    Parses an ingredients dictionary to create a new dictionary
    based on the filter_word as the key.

    Parameters
    ----------
    ingredients_dict : dict
    filter_word : str
    remove_prefix : bool, optional

    Returns
    -------
    parsed_ingredient_dict : str (JSON)
    """
    parsed_ingredient_dict = {}
    for key in list(ingredients_dict.keys()):
        if filter_word in key and ingredients_dict[key] != '':
            if not remove_prefix:
                new_key = key.replace(filter_word, '')
            else:
                new_key = key.removeprefix(filter_word)
            parsed_ingredient_dict[new_key] = ingredients_dict[key]
    return json.dumps(parsed_ingredient_dict)


def get_tag_keys(tags):
    tag_list = []
    for tag_dict in tags:
        if list(tag_dict.values())[0] == 1:
            tag_list.append(list(tag_dict.keys())[0])
    return tag_list


def get_tags(tags):
    from .variables import tag_list, tag_list_backend
    parsed_tags = {}
    for tag in tag_list:
        if tag in tags:
            parsed_tags[tag.replace('/', '_')] = "1"
        else:
            parsed_tags[tag.replace('/', '_')] = "0"
    return parsed_tags
