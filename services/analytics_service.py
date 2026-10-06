from collections import Counter
from datetime import datetime

from services.order_storage import load_orders


# ============================================================
# LOAD CONFIRMED ORDERS
# ============================================================

def get_orders():
    return load_orders()


# ============================================================
# BASIC KPI DATA
# ============================================================

def get_total_orders():

    orders = get_orders()

    return len(orders)


def get_total_revenue():

    orders = get_orders()

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


def get_average_order_value():

    orders = get_orders()

    if not orders:
        return 0

    revenue = get_total_revenue()

    return round(
        revenue / len(orders),
        2,
    )


def get_total_items_sold():

    orders = get_orders()

    total_items = 0

    for order in orders:

        total_items += int(
            order.get(
                "item_count",
                0,
            )
        )

    return total_items


# ============================================================
# ITEM SALES
# ============================================================

def get_item_sales():

    orders = get_orders()

    item_counter = Counter()


    for order in orders:

        for item in order.get(
            "items",
            [],
        ):

            name = item.get(
                "name",
                "Unknown Item",
            )

            quantity = int(
                item.get(
                    "quantity",
                    0,
                )
            )

            item_counter[name] += quantity


    return dict(
        item_counter.most_common()
    )


# ============================================================
# TOP SELLING ITEMS
# ============================================================

def get_top_selling_items(
    limit=10,
):

    item_sales = get_item_sales()

    return dict(
        list(
            item_sales.items()
        )[:limit]
    )


# ============================================================
# ALCOHOL VS NON-ALCOHOL ORDERS
# ============================================================

def get_alcohol_order_split():

    orders = get_orders()

    alcoholic_orders = 0

    non_alcoholic_orders = 0


    for order in orders:

        if order.get(
            "contains_alcohol",
            False,
        ):

            alcoholic_orders += 1

        else:

            non_alcoholic_orders += 1


    return {

        "Alcoholic": alcoholic_orders,

        "Non-Alcoholic": non_alcoholic_orders,
    }


# ============================================================
# VEGETARIAN VS NON-VEGETARIAN ITEM DEMAND
# ============================================================

def get_vegetarian_split():

    orders = get_orders()

    vegetarian_items = 0

    non_vegetarian_items = 0

    unknown_items = 0


    # Import only when needed to avoid unnecessary
    # dependency loading at module initialization.

    from services.catalog_service import get_item_by_id


    for order in orders:

        for item in order.get(
            "items",
            [],
        ):

            item_id = item.get(
                "item_id"
            )

            quantity = int(
                item.get(
                    "quantity",
                    0,
                )
            )


            catalog_item = get_item_by_id(
                item_id
            )


            if not catalog_item:

                unknown_items += quantity

                continue


            vegetarian = catalog_item.get(
                "vegetarian"
            )


            if vegetarian is True:

                vegetarian_items += quantity

            elif vegetarian is False:

                non_vegetarian_items += quantity

            else:

                unknown_items += quantity


    result = {

        "Vegetarian": vegetarian_items,

        "Non-Vegetarian": non_vegetarian_items,
    }


    if unknown_items > 0:

        result["Other"] = unknown_items


    return result


# ============================================================
# REVENUE BY ORDER
# ============================================================

def get_revenue_by_order():

    orders = get_orders()

    revenue_data = []


    for order in orders:

        revenue_data.append({

            "Order ID": order.get(
                "order_id",
                "Unknown",
            ),

            "Revenue": float(
                order.get(
                    "total",
                    0,
                )
            ),

            "Date": order.get(
                "confirmed_at",
                "",
            ),
        })


    return revenue_data


# ============================================================
# RECENT ORDERS
# ============================================================

def get_recent_orders(
    limit=10,
):

    orders = get_orders()

    return list(
        reversed(orders)
    )[:limit]


# ============================================================
# REVENUE BY DATE
# ============================================================

def get_revenue_by_date():

    orders = get_orders()

    revenue_by_date = {}


    for order in orders:

        timestamp = order.get(
            "confirmed_at",
            "",
        )


        if not timestamp:

            continue


        try:

            date_value = (
                datetime.strptime(
                    timestamp,
                    "%d %b %Y, %I:%M %p",
                )
                .strftime(
                    "%d %b %Y"
                )
            )

        except ValueError:

            date_value = (
                timestamp.split(",")[0]
                if "," in timestamp
                else timestamp
            )


        revenue_by_date[date_value] = (
            revenue_by_date.get(
                date_value,
                0,
            )
            + float(
                order.get(
                    "total",
                    0,
                )
            )
        )


    return revenue_by_date


# ============================================================
# COMPLETE DASHBOARD SUMMARY
# ============================================================

def get_dashboard_summary():

    return {

        "total_orders": get_total_orders(),

        "total_revenue": get_total_revenue(),

        "average_order_value": (
            get_average_order_value()
        ),

        "total_items_sold": (
            get_total_items_sold()
        ),

        "top_selling_items": (
            get_top_selling_items()
        ),

        "alcohol_order_split": (
            get_alcohol_order_split()
        ),

        "vegetarian_split": (
            get_vegetarian_split()
        ),

        "recent_orders": (
            get_recent_orders()
        ),
    }