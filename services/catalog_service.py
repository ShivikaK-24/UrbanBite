import json
from pathlib import Path


# ---------------------------------------------------------
# LOAD MASTER CATALOG
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
MENU_PATH = BASE_DIR / "data" / "menu.json"


def load_catalog():
    """Load the complete restaurant catalog from menu.json."""

    with open(MENU_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


# ---------------------------------------------------------
# BASIC ACCESS
# ---------------------------------------------------------

def get_all_items():
    """Return all menu items."""

    catalog = load_catalog()
    return catalog.get("items", [])


def get_restaurant_info():
    """Return restaurant-level information."""

    catalog = load_catalog()
    return catalog.get("restaurant", {})


# ---------------------------------------------------------
# SEARCH
# ---------------------------------------------------------

def search_menu(query):
    """
    Search the menu using item name, category,
    subcategory and description.
    """

    query = query.lower().strip()

    if not query:
        return []

    results = []

    for item in get_all_items():

        searchable_text = " ".join([
            str(item.get("name", "")),
            str(item.get("category", "")),
            str(item.get("subcategory", "")),
            str(item.get("description", ""))
        ]).lower()

        if query in searchable_text:
            results.append(item)

    return results


# ---------------------------------------------------------
# EXACT ITEM LOOKUP
# ---------------------------------------------------------

def get_item_by_id(item_id):
    """Find an item using its unique ID."""

    for item in get_all_items():

        if item.get("id") == item_id:
            return item

    return None


def get_item_by_name(name):
    """Find an item using its exact name."""

    name = name.lower().strip()

    for item in get_all_items():

        if item.get("name", "").lower() == name:
            return item

    return None


# ---------------------------------------------------------
# CATEGORY FILTERING
# ---------------------------------------------------------

def get_categories():
    """Return unique top-level categories."""

    categories = set()

    for item in get_all_items():
        category = item.get("category")

        if category:
            categories.add(category)

    return sorted(categories)


def get_subcategories():
    """Return unique menu subcategories."""

    subcategories = set()

    for item in get_all_items():
        subcategory = item.get("subcategory")

        if subcategory:
            subcategories.add(subcategory)

    return sorted(subcategories)


def get_items_by_category(category):
    """Return items belonging to a category."""

    category = category.lower().strip()

    return [
        item
        for item in get_all_items()
        if item.get("category", "").lower() == category
    ]


def get_items_by_subcategory(subcategory):
    """Return items belonging to a subcategory."""

    subcategory = subcategory.lower().strip()

    return [
        item
        for item in get_all_items()
        if item.get("subcategory", "").lower() == subcategory
    ]


# ---------------------------------------------------------
# VEGETARIAN / NON-VEGETARIAN
# ---------------------------------------------------------

def get_vegetarian_items():
    """Return vegetarian items only."""

    return [
        item
        for item in get_all_items()
        if item.get("vegetarian") is True
    ]


def get_non_vegetarian_items():
    """Return non-vegetarian items only."""

    return [
        item
        for item in get_all_items()
        if item.get("vegetarian") is False
    ]


# ---------------------------------------------------------
# ALCOHOL
# ---------------------------------------------------------

def get_alcoholic_items():
    """Return alcoholic items only."""

    return [
        item
        for item in get_all_items()
        if item.get("alcoholic") is True
    ]


def get_non_alcoholic_items():
    """Return non-alcoholic items."""

    return [
        item
        for item in get_all_items()
        if item.get("alcoholic") is False
    ]


# ---------------------------------------------------------
# PRICE FILTER
# ---------------------------------------------------------

def get_items_under_price(max_price):
    """Return items whose base price is within the budget."""

    results = []

    for item in get_all_items():

        price = item.get("base_price")

        if price is not None and price <= max_price:
            results.append(item)

        # Also check variants
        for variant in item.get("variants", []):

            variant_price = variant.get("price")

            if variant_price is not None and variant_price <= max_price:
                if item not in results:
                    results.append(item)

    return results


# ---------------------------------------------------------
# MENU SUMMARY
# ---------------------------------------------------------

def get_catalog_summary():
    """Return useful statistics for the application."""

    items = get_all_items()

    return {
        "total_items": len(items),
        "categories": len(get_categories()),
        "subcategories": len(get_subcategories()),
        "vegetarian_items": len(get_vegetarian_items()),
        "non_vegetarian_items": len(get_non_vegetarian_items()),
        "alcoholic_items": len(get_alcoholic_items()),
    }