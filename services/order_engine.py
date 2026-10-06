from datetime import datetime
import random

from services.catalog_service import (
    get_item_by_id,
    get_restaurant_info,
)

from services.order_storage import save_order


class OrderEngine:

    def __init__(self):
        self.items = []


    # ========================================================
    # ADD ITEM
    # ========================================================

    def add_item(
        self,
        item_id,
        quantity=1,
        variant=None,
        modifiers=None,
    ):

        item = get_item_by_id(item_id)

        if not item:

            return {
                "success": False,
                "message": "Item not found.",
            }


        if quantity < 1:

            return {
                "success": False,
                "message": "Quantity must be at least 1.",
            }


        modifiers = modifiers or []


        # ----------------------------------------------------
        # DETERMINE PRICE
        # ----------------------------------------------------

        price = item.get(
            "base_price"
        )

        selected_variant = variant


        if variant:

            for v in item.get(
                "variants",
                [],
            ):

                if (
                    v.get("name", "").lower()
                    == variant.lower()
                ):

                    price = v.get(
                        "price"
                    )

                    selected_variant = v.get(
                        "name"
                    )

                    break


        if price is None:

            return {
                "success": False,
                "message": (
                    "Price could not be determined."
                ),
            }


        # ----------------------------------------------------
        # MERGE IDENTICAL CART ITEMS
        # ----------------------------------------------------

        for existing_item in self.items:

            same_item = (
                existing_item["item_id"]
                == item_id
            )

            same_variant = (
                existing_item.get("variant")
                == selected_variant
            )

            same_modifiers = (
                existing_item.get("modifiers", [])
                == modifiers
            )


            if (
                same_item
                and same_variant
                and same_modifiers
            ):

                existing_item["quantity"] += (
                    quantity
                )


                return {
                    "success": True,
                    "message": (
                        f"{quantity} × "
                        f"{item.get('name')} "
                        "added to your order."
                    ),
                    "item": existing_item,
                    "order": self.get_order_summary(),
                }


        # ----------------------------------------------------
        # CREATE NEW CART ITEM
        # ----------------------------------------------------

        order_item = {

            "item_id": item_id,

            "name": item.get(
                "name"
            ),

            "quantity": quantity,

            "unit_price": price,

            "variant": selected_variant,

            "modifiers": modifiers,

            "alcoholic": item.get(
                "alcoholic",
                False,
            ),
        }


        self.items.append(
            order_item
        )


        return {

            "success": True,

            "message": (
                f"{quantity} × "
                f"{item.get('name')} "
                "added to your order."
            ),

            "item": order_item,

            "order": self.get_order_summary(),
        }


    # ========================================================
    # REMOVE ITEM
    # ========================================================

    def remove_item(
        self,
        item_id,
        variant=None,
    ):

        original_count = len(
            self.items
        )


        if variant is None:

            self.items = [

                item

                for item in self.items

                if item["item_id"] != item_id

            ]

        else:

            self.items = [

                item

                for item in self.items

                if not (
                    item["item_id"] == item_id
                    and item.get("variant")
                    == variant
                )

            ]


        if len(self.items) == original_count:

            return {

                "success": False,

                "message": (
                    "Item was not in the order."
                ),
            }


        return {

            "success": True,

            "message": "Item removed.",

            "order": self.get_order_summary(),
        }


    # ========================================================
    # CLEAR ORDER
    # ========================================================

    def clear_order(self):

        self.items = []


        return {

            "success": True,

            "message": "Order cleared.",
        }


    # ========================================================
    # SUBTOTAL
    # ========================================================

    def calculate_subtotal(self):

        subtotal = 0


        for item in self.items:

            subtotal += (
                item["unit_price"]
                * item["quantity"]
            )


        return round(
            subtotal,
            2,
        )


    # ========================================================
    # TAX
    # ========================================================

    def calculate_tax(self):

        restaurant_info = (
            get_restaurant_info()
        )


        tax_rate = restaurant_info.get(
            "tax_rate",
            0,
        )


        subtotal = (
            self.calculate_subtotal()
        )


        tax = subtotal * tax_rate


        return round(
            tax,
            2,
        )


    # ========================================================
    # TOTAL
    # ========================================================

    def calculate_total(self):

        subtotal = (
            self.calculate_subtotal()
        )

        tax = (
            self.calculate_tax()
        )


        return round(
            subtotal + tax,
            2,
        )


    # ========================================================
    # ALCOHOL CHECK
    # ========================================================

    def contains_alcohol(self):

        return any(
            item.get(
                "alcoholic",
                False,
            )

            for item in self.items
        )


    # ========================================================
    # ORDER SUMMARY
    # ========================================================

    def get_order_summary(self):

        subtotal = (
            self.calculate_subtotal()
        )

        tax = (
            self.calculate_tax()
        )

        total = (
            self.calculate_total()
        )


        return {

            "items": self.items,

            "item_count": sum(
                item["quantity"]
                for item in self.items
            ),

            "subtotal": subtotal,

            "tax": tax,

            "tax_rate": (
                get_restaurant_info()
                .get(
                    "tax_rate",
                    0,
                )
            ),

            "total": total,

            "contains_alcohol": (
                self.contains_alcohol()
            ),
        }


    # ========================================================
    # CHECKOUT VALIDATION
    # ========================================================

    def validate_checkout(
        self,
        age_verified=False,
    ):

        if not self.items:

            return {

                "success": False,

                "message": (
                    "Your order is empty."
                ),
            }


        if (
            self.contains_alcohol()
            and not age_verified
        ):

            return {

                "success": False,

                "requires_age_verification": True,

                "message": (
                    "Your order contains alcohol. "
                    "Please confirm that you are "
                    "25 years or older."
                ),
            }


        return {

            "success": True,

            "requires_age_verification": (
                self.contains_alcohol()
            ),

            "message": (
                "Order is ready for confirmation."
            ),
        }


    # ========================================================
    # GENERATE ORDER ID
    # ========================================================

    def generate_order_id(self):

        date_part = (
            datetime.now().strftime(
                "%Y%m%d"
            )
        )


        random_part = (
            f"{random.randint(1000, 9999)}"
        )


        return (
            f"UB-{date_part}-{random_part}"
        )


    # ========================================================
    # CONFIRM ORDER
    # ========================================================

    def confirm_order(
        self,
        age_verified=False,
    ):

        validation = (
            self.validate_checkout(
                age_verified=age_verified
            )
        )


        if not validation["success"]:

            return validation


        summary = (
            self.get_order_summary()
        )


        order_id = (
            self.generate_order_id()
        )


        confirmed_at = (
            datetime.now().strftime(
                "%d %b %Y, %I:%M %p"
            )
        )


        confirmed_order = {

            "order_id": order_id,

            "restaurant": (
                get_restaurant_info()
                .get(
                    "name",
                    "UrbanBite",
                )
            ),

            "items": [
                dict(item)
                for item in summary["items"]
            ],

            "item_count": (
                summary["item_count"]
            ),

            "subtotal": (
                summary["subtotal"]
            ),

            "tax_rate": (
                summary["tax_rate"]
            ),

            "tax": (
                summary["tax"]
            ),

            "total": (
                summary["total"]
            ),

            "contains_alcohol": (
                summary["contains_alcohol"]
            ),

            "age_verified": (
                age_verified
            ),

            "confirmed_at": confirmed_at,
        }


        # ----------------------------------------------------
        # SAVE CONFIRMED ORDER
        # ----------------------------------------------------

        save_order(
            confirmed_order
        )


        return {

            "success": True,

            "message": (
                "Order confirmed successfully."
            ),

            "order": confirmed_order,
        }