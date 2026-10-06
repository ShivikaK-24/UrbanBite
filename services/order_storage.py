import json
from pathlib import Path


# ============================================================
# FILE LOCATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ORDERS_PATH = BASE_DIR / "data" / "orders.json"


# ============================================================
# ENSURE FILE EXISTS
# ============================================================

def ensure_orders_file():

    ORDERS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not ORDERS_PATH.exists():

        with open(
            ORDERS_PATH,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                [],
                file,
                indent=4,
            )


# ============================================================
# LOAD ORDERS
# ============================================================

def load_orders():

    ensure_orders_file()


    try:

        with open(
            ORDERS_PATH,
            "r",
            encoding="utf-8",
        ) as file:

            orders = json.load(file)


        if isinstance(orders, list):

            return orders


        return []


    except (
        json.JSONDecodeError,
        OSError,
    ):

        return []


# ============================================================
# SAVE ALL ORDERS
# ============================================================

def save_orders(orders):

    ensure_orders_file()


    with open(
        ORDERS_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            orders,
            file,
            indent=4,
            ensure_ascii=False,
        )


# ============================================================
# SAVE ONE ORDER
# ============================================================

def save_order(order):

    orders = load_orders()


    orders.append(
        order
    )


    save_orders(
        orders
    )


    return order


# ============================================================
# GET ORDER BY ID
# ============================================================

def get_order_by_id(order_id):

    orders = load_orders()


    for order in orders:

        if order.get(
            "order_id"
        ) == order_id:

            return order


    return None


# ============================================================
# GET ORDER COUNT
# ============================================================

def get_order_count():

    return len(
        load_orders()
    )


# ============================================================
# GET TOTAL REVENUE
# ============================================================

def get_total_revenue():

    orders = load_orders()


    total = 0


    for order in orders:

        total += float(
            order.get(
                "total",
                0,
            )
        )


    return round(
        total,
        2,
    )