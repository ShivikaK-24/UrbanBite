import re

import streamlit as st
import pandas as pd

from services.catalog_service import (
    get_all_items,
    get_items_by_category,
)

from services.order_engine import OrderEngine

from services.ai_service import (
    get_ai_action,
)

from services.auth_service import (
    is_staff_logged_in,
    login_staff,
    logout_staff,
)

from services.analytics_service import (
    get_total_orders,
    get_total_revenue,
    get_average_order_value,
    get_total_items_sold,
    get_top_selling_items,
    get_alcohol_order_split,
    get_recent_orders,
    get_revenue_by_order,
)

from services.manager_insights import (
    generate_manager_insights,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="OrderIQ | UrbanBite",
    page_icon="🍔",
    layout="wide",
)


# ============================================================
# SESSION STATE
# ============================================================

if "order_engine" not in st.session_state:

    st.session_state.order_engine = (
        OrderEngine()
    )


if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Good evening 👋\n\n"
                "I'm your UrbanBite ordering assistant. "
                "Tell me what you're craving, and I'll help "
                "you find the right dishes and drinks."
            ),
        }
    ]


if "age_verified" not in st.session_state:

    st.session_state.age_verified = False


if "confirmed_order" not in st.session_state:

    st.session_state.confirmed_order = None


if "current_page" not in st.session_state:

    st.session_state.current_page = (
        "Customer Ordering"
    )


# ============================================================
# LOAD CATALOG
# ============================================================

all_items = get_all_items()


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text):

    if not text:
        return ""

    text = str(text).lower()

    text = text.replace(
        "&",
        " and "
    )

    text = re.sub(
        r"[^a-z0-9₹ ]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def singularize_word(word):

    word = word.lower().strip()

    if word.endswith("ies"):

        return word[:-3] + "y"

    if word.endswith("es") and len(word) > 4:

        return word[:-2]

    if word.endswith("s") and len(word) > 3:

        return word[:-1]

    return word


def extract_price_limit(query):

    query = normalize_text(query)

    patterns = [
        r"under\s+₹?\s*(\d+)",
        r"below\s+₹?\s*(\d+)",
        r"less than\s+₹?\s*(\d+)",
        r"within\s+₹?\s*(\d+)",
        r"upto\s+₹?\s*(\d+)",
        r"up to\s+₹?\s*(\d+)",
        r"₹\s*(\d+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            query,
        )

        if match:

            return float(
                match.group(1)
            )

    return None


# ============================================================
# MENU RETRIEVAL
# ============================================================

def retrieve_menu_items(
    user_query,
    max_items=40,
):

    query = normalize_text(
        user_query
    )

    if not query:

        return all_items[:max_items]

    tokens = {
        singularize_word(token)
        for token in query.split()
        if len(token) >= 3
    }

    vegetarian_request = any(
        phrase in query
        for phrase in [
            "vegetarian",
            "vegetarian food",
            "veg food",
            "veg options",
            "veg dishes",
        ]
    )

    alcohol_request = any(
        phrase in query
        for phrase in [
            "alcohol",
            "alcoholic",
            "bar",
            "cocktail",
            "cocktails",
            "beer",
            "wine",
            "whisky",
            "whiskey",
            "vodka",
            "gin",
            "rum",
            "tequila",
            "brandy",
            "cognac",
            "champagne",
            "sangria",
            "liqueur",
            "aperitif",
            "shooter",
        ]
    )

    beverage_request = any(
        phrase in query
        for phrase in [
            "drink",
            "drinks",
            "beverage",
            "beverages",
            "coffee",
            "tea",
            "shake",
            "shakes",
            "cooler",
            "coolers",
            "juice",
        ]
    )

    food_request = any(
        phrase in query
        for phrase in [
            "food",
            "dish",
            "dishes",
            "meal",
            "dinner",
            "lunch",
            "starter",
            "starters",
            "main",
            "mains",
            "dessert",
        ]
    )

    price_limit = extract_price_limit(
        query
    )

    scored_items = []

    for item in all_items:

        name = normalize_text(
            item.get("name", "")
        )

        category = normalize_text(
            item.get("category", "")
        )

        subcategory = normalize_text(
            item.get("subcategory", "")
        )

        description = normalize_text(
            item.get("description", "")
        )

        score = 0

        if name == query:

            score += 100

        if query in name:

            score += 80

        name_tokens = {
            singularize_word(token)
            for token in name.split()
            if len(token) >= 3
        }

        subcategory_tokens = {
            singularize_word(token)
            for token in subcategory.split()
            if len(token) >= 3
        }

        category_tokens = {
            singularize_word(token)
            for token in category.split()
            if len(token) >= 3
        }

        description_tokens = {
            singularize_word(token)
            for token in description.split()
            if len(token) >= 3
        }

        score += (
            len(tokens & name_tokens)
            * 25
        )

        score += (
            len(tokens & subcategory_tokens)
            * 30
        )

        score += (
            len(tokens & category_tokens)
            * 15
        )

        score += (
            len(tokens & description_tokens)
            * 5
        )

        if vegetarian_request:

            if item.get("vegetarian") is True:

                score += 60

            else:

                score -= 100

        if alcohol_request:

            if item.get("alcoholic") is True:

                score += 60

            else:

                score -= 100

        if beverage_request:

            if item.get("category") in [
                "Beverages",
                "Alcohol",
            ]:

                score += 40

        if food_request:

            if item.get("category") == "Food":

                score += 30

        if price_limit is not None:

            prices = []

            if item.get("base_price") is not None:

                prices.append(
                    float(
                        item.get(
                            "base_price"
                        )
                    )
                )

            for variant in item.get(
                "variants",
                [],
            ):

                if variant.get("price") is not None:

                    prices.append(
                        float(
                            variant.get("price")
                        )
                    )

            if prices:

                if min(prices) <= price_limit:

                    score += 40

                else:

                    score -= 100

        if score > 0:

            scored_items.append(
                (
                    score,
                    item,
                )
            )

    scored_items.sort(
        key=lambda x: x[0],
        reverse=True,
    )

    results = []

    seen_ids = set()

    for score, item in scored_items:

        item_id = item.get("id")

        if item_id in seen_ids:

            continue

        seen_ids.add(
            item_id
        )

        results.append(
            item
        )

        if len(results) >= max_items:

            break

    if not results:

        if vegetarian_request:

            results = [
                item
                for item in all_items
                if item.get(
                    "vegetarian"
                ) is True
            ][:max_items]

        elif alcohol_request:

            results = [
                item
                for item in all_items
                if item.get(
                    "alcoholic"
                ) is True
            ][:max_items]

        elif beverage_request:

            results = [
                item
                for item in all_items
                if item.get(
                    "category"
                ) in [
                    "Beverages",
                    "Alcohol",
                ]
            ][:max_items]

        elif food_request:

            results = [
                item
                for item in all_items
                if item.get(
                    "category"
                ) == "Food"
            ][:max_items]

        else:

            results = all_items[:max_items]

    return results


# ============================================================
# FIND CATALOG ITEM
# ============================================================

def find_catalog_item(
    item_id=None,
    item_name=None,
):

    if item_id:

        for item in all_items:

            if item.get("id") == item_id:

                return item

    if item_name:

        normalized_name = normalize_text(
            item_name
        )

        for item in all_items:

            catalog_name = normalize_text(
                item.get(
                    "name",
                    ""
                )
            )

            if catalog_name == normalized_name:

                return item

    return None


# ============================================================
# VALIDATE VARIANT
# ============================================================

def validate_variant(
    item,
    requested_variant,
):

    if not requested_variant:

        return None

    variants = item.get(
        "variants",
        []
    )

    for variant in variants:

        if normalize_text(
            variant.get(
                "name",
                ""
            )
        ) == normalize_text(
            requested_variant
        ):

            return variant.get(
                "name"
            )

    return None


# ============================================================
# EXECUTE AI CART ACTION
# ============================================================

def execute_ai_action(
    ai_action
):

    action = ai_action.get(
        "action"
    )

    item_id = ai_action.get(
        "item_id"
    )

    item_name = ai_action.get(
        "item_name"
    )

    quantity = ai_action.get(
        "quantity",
        1,
    )

    variant = ai_action.get(
        "variant"
    )

    item = find_catalog_item(
        item_id=item_id,
        item_name=item_name,
    )

    if not item:

        return {
            "success": False,
            "message": (
                "I couldn't find that item "
                "in the UrbanBite menu."
            ),
        }

    real_item_id = item.get(
        "id"
    )

    real_item_name = item.get(
        "name"
    )

    try:

        quantity = int(
            quantity
        )

    except (
        TypeError,
        ValueError,
    ):

        quantity = 1

    if quantity < 1:

        quantity = 1

    validated_variant = validate_variant(
        item,
        variant,
    )

    if variant and not validated_variant:

        return {
            "success": False,
            "message": (
                f"I couldn't find the "
                f"{variant} variant of "
                f"{real_item_name}."
            ),
        }

    if action == "ADD_ITEM":

        result = (
            st.session_state
            .order_engine
            .add_item(
                item_id=real_item_id,
                quantity=quantity,
                variant=validated_variant,
            )
        )

        if result["success"]:

            return {
                "success": True,
                "message": (
                    f"Added {quantity} × "
                    f"{real_item_name} "
                    "to your cart."
                ),
            }

        return {
            "success": False,
            "message": result["message"],
        }

    if action == "REMOVE_ITEM":

        result = (
            st.session_state
            .order_engine
            .remove_item(
                real_item_id,
                validated_variant,
            )
        )

        if result["success"]:

            return {
                "success": True,
                "message": (
                    f"Removed {real_item_name} "
                    "from your cart."
                ),
            }

        return {
            "success": False,
            "message": (
                f"{real_item_name} "
                "is not currently in your cart."
            ),
        }

    if action == "UPDATE_QUANTITY":

        st.session_state.order_engine.remove_item(
            real_item_id,
            validated_variant,
        )

        add_result = (
            st.session_state
            .order_engine
            .add_item(
                item_id=real_item_id,
                quantity=quantity,
                variant=validated_variant,
            )
        )

        if add_result["success"]:

            return {
                "success": True,
                "message": (
                    f"Updated {real_item_name} "
                    f"to {quantity}."
                ),
            }

        return {
            "success": False,
            "message": add_result["message"],
        }

    return {
        "success": True,
        "message": ai_action.get(
            "response",
            "How can I help you?",
        ),
    }


# ============================================================
# PROCESS USER MESSAGE
# ============================================================

def process_user_message(
    user_message
):

    relevant_items = retrieve_menu_items(
        user_message,
        max_items=40,
    )

    ai_action = get_ai_action(
        user_message=user_message,
        relevant_items=relevant_items,
        conversation_history=(
            st.session_state.messages[:-1]
        ),
    )

    action = ai_action.get(
        "action"
    )

    if action in [
        "ADD_ITEM",
        "REMOVE_ITEM",
        "UPDATE_QUANTITY",
    ]:

        result = execute_ai_action(
            ai_action
        )

        return result["message"]

    return ai_action.get(
        "response",
        "How can I help you?",
    )


# ============================================================
# CONFIRMED ORDER
# ============================================================

def display_confirmed_order(
    order
):

    st.success(
        "🎉 Order Confirmed!"
    )

    st.subheader(
        "Your UrbanBite order is confirmed",
        anchor=False,
    )

    st.metric(
        "Order ID",
        order["order_id"],
    )

    st.caption(
        order["confirmed_at"]
    )

    st.divider()

    for item in order["items"]:

        quantity = item[
            "quantity"
        ]

        name = item[
            "name"
        ]

        unit_price = item[
            "unit_price"
        ]

        line_total = (
            quantity
            * unit_price
        )

        if item.get(
            "variant"
        ):

            st.write(
                f"**{quantity} × {name} "
                f"({item['variant']})**"
            )

        else:

            st.write(
                f"**{quantity} × {name}**"
            )

        st.caption(
            f"₹{line_total:,.2f}"
        )

    st.divider()

    summary_col, value_col = (
        st.columns(
            [3, 1]
        )
    )

    with summary_col:

        st.write(
            "Subtotal"
        )

        st.write(
            f"GST ({order['tax_rate'] * 100:.0f}%)"
        )

        st.write(
            "**Total**"
        )

    with value_col:

        st.write(
            f"₹{order['subtotal']:,.2f}"
        )

        st.write(
            f"₹{order['tax']:,.2f}"
        )

        st.write(
            f"**₹{order['total']:,.2f}**"
        )

    if order[
        "age_verified"
    ]:

        st.caption(
            "🍸 Age verification completed"
        )

    st.info(
        "Thank you for ordering with UrbanBite! "
        "Your order has been successfully recorded."
    )


# ============================================================
# STAFF LOGIN
# ============================================================

def render_staff_login():

    st.title(
        "🔐 Staff Login",
        anchor=False,
    )

    st.caption(
        "UrbanBite management portal"
    )

    st.divider()

    left, center, right = (
        st.columns(
            [1, 2, 1]
        )
    )

    with center:

        with st.container(
            border=True
        ):

            st.subheader(
                "Manager Access",
                anchor=False,
            )

            st.write(
                "Sign in to access restaurant "
                "performance and AI-powered "
                "management insights."
            )

            username = st.text_input(
                "Username",
                placeholder=(
                    "Enter staff username"
                ),
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder=(
                    "Enter password"
                ),
            )

            if st.button(
                "Sign In",
                type="primary",
                use_container_width=True,
            ):

                if login_staff(
                    username,
                    password,
                ):

                    st.session_state.current_page = (
                        "Manager Dashboard"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Invalid username or password."
                    )

            st.caption(
                "Staff access only."
            )


# ============================================================
# AI MANAGER INSIGHTS
# ============================================================

def render_ai_manager_insights():

    st.subheader(
        "🤖 AI Manager Insights",
        anchor=False,
    )

    st.write(
        "Use the confirmed order data to generate "
        "AI-powered business observations and "
        "actionable recommendations."
    )

    st.caption(
        "The AI analyzes existing OrderIQ data. "
        "It does not create or modify orders."
    )

    if st.button(
        "✨ Generate AI Insights",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Analyzing UrbanBite business data..."
        ):

            try:

                insights = (
                    generate_manager_insights()
                )

                st.session_state[
                    "manager_insights"
                ] = insights

            except Exception as error:

                st.error(
                    "Unable to generate AI insights."
                )

                st.caption(
                    str(error)
                )

    insights = st.session_state.get(
        "manager_insights"
    )

    if not insights:

        st.info(
            "Click **Generate AI Insights** "
            "to analyze the current restaurant data."
        )

        return

    st.divider()

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    st.markdown(
        "### 🧠 Executive Summary"
    )

    st.info(
        insights.get(
            "executive_summary",
            "No summary available.",
        )
    )

    # ========================================================
    # OBSERVATIONS
    # ========================================================

    st.markdown(
        "### 🔎 Key Observations"
    )

    observations = insights.get(
        "key_observations",
        [],
    )

    for observation in observations:

        st.write(
            f"• {observation}"
        )

    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    st.markdown(
        "### 💡 Recommended Actions"
    )

    recommendations = insights.get(
        "recommendations",
        [],
    )

    for index, recommendation in enumerate(
        recommendations,
        start=1,
    ):

        action = recommendation.get(
            "action",
            "Recommended action",
        )

        reason = recommendation.get(
            "reason",
            "",
        )

        with st.container(
            border=True
        ):

            st.markdown(
                f"**{index}. {action}**"
            )

            if reason:

                st.write(
                    reason
                )

    # ========================================================
    # DATA CAVEAT
    # ========================================================

    caveat = insights.get(
        "data_caveat"
    )

    if caveat:

        st.warning(
            f"⚠️ Data limitation: {caveat}"
        )


# ============================================================
# MANAGER DASHBOARD
# ============================================================

def render_manager_dashboard():

    st.title(
        "📊 Manager Dashboard",
        anchor=False,
    )

    st.caption(
        "UrbanBite · Restaurant performance overview"
    )

    st.divider()

    header_left, header_right = (
        st.columns(
            [5, 1]
        )
    )

    with header_left:

        st.subheader(
            "Business Overview",
            anchor=False,
        )

        st.write(
            "Monitor orders, revenue, customer demand "
            "and AI-generated management insights."
        )

    with header_right:

        if st.button(
            "Log Out",
            use_container_width=True,
        ):

            logout_staff()

            st.session_state.current_page = (
                "Customer Ordering"
            )

            st.rerun()

    # ========================================================
    # KPIs
    # ========================================================

    total_orders = get_total_orders()

    total_revenue = get_total_revenue()

    average_order_value = (
        get_average_order_value()
    )

    total_items_sold = (
        get_total_items_sold()
    )

    kpi_1, kpi_2, kpi_3, kpi_4 = (
        st.columns(4)
    )

    with kpi_1:

        st.metric(
            "🧾 Total Orders",
            total_orders,
        )

    with kpi_2:

        st.metric(
            "💰 Revenue",
            f"₹{total_revenue:,.2f}",
        )

    with kpi_3:

        st.metric(
            "🛒 Avg. Order Value",
            f"₹{average_order_value:,.2f}",
        )

    with kpi_4:

        st.metric(
            "🍽️ Items Sold",
            total_items_sold,
        )

    st.divider()

    # ========================================================
    # AI INSIGHTS FIRST
    # ========================================================

    render_ai_manager_insights()

    st.divider()

    # ========================================================
    # TOP SELLING ITEMS
    # ========================================================

    st.subheader(
        "🏆 Top-Selling Menu Items",
        anchor=False,
    )

    top_items = get_top_selling_items(
        limit=10
    )

    if top_items:

        top_items_df = pd.DataFrame(
            {
                "Item": list(
                    top_items.keys()
                ),
                "Quantity Sold": list(
                    top_items.values()
                ),
            }
        )

        st.bar_chart(
            top_items_df.set_index(
                "Item"
            )
        )

    else:

        st.info(
            "No item sales data available yet."
        )

    st.divider()

    # ========================================================
    # ORDER MIX
    # ========================================================

    st.subheader(
        "🍸 Order Mix",
        anchor=False,
    )

    alcohol_split = (
        get_alcohol_order_split()
    )

    alcohol_df = pd.DataFrame(
        {
            "Order Type": list(
                alcohol_split.keys()
            ),
            "Orders": list(
                alcohol_split.values()
            ),
        }
    )

    if alcohol_df["Orders"].sum() > 0:

        st.bar_chart(
            alcohol_df.set_index(
                "Order Type"
            )
        )

    else:

        st.info(
            "No order mix data available yet."
        )

    st.divider()

    # ========================================================
    # REVENUE BY ORDER
    # ========================================================

    st.subheader(
        "📈 Revenue by Order",
        anchor=False,
    )

    revenue_data = (
        get_revenue_by_order()
    )

    if revenue_data:

        revenue_df = pd.DataFrame(
            revenue_data
        )

        revenue_df = revenue_df[
            [
                "Order ID",
                "Revenue",
            ]
        ]

        revenue_df = revenue_df.set_index(
            "Order ID"
        )

        st.line_chart(
            revenue_df
        )

    else:

        st.info(
            "No revenue data available yet."
        )

    st.divider()

    # ========================================================
    # RECENT ORDERS
    # ========================================================

    st.subheader(
        "📋 Recent Orders",
        anchor=False,
    )

    recent_orders = get_recent_orders(
        limit=10
    )

    if recent_orders:

        recent_rows = []

        for order in recent_orders:

            item_summary = ", ".join(
                [
                    (
                        f"{item.get('quantity', 0)} × "
                        f"{item.get('name', 'Unknown')}"
                    )

                    for item in order.get(
                        "items",
                        [],
                    )
                ]
            )

            recent_rows.append(
                {
                    "Order ID": order.get(
                        "order_id",
                        "",
                    ),
                    "Time": order.get(
                        "confirmed_at",
                        "",
                    ),
                    "Items": item_summary,
                    "Total": (
                        f"₹{float(order.get('total', 0)):,.2f}"
                    ),
                }
            )

        recent_df = pd.DataFrame(
            recent_rows
        )

        st.dataframe(
            recent_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No confirmed orders yet."
        )

    st.divider()

    st.caption(
        "Data shown above is generated from confirmed "
        "UrbanBite orders stored by OrderIQ."
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "🍔 OrderIQ"
    )

    st.caption(
        "UrbanBite"
    )

    st.divider()

    if is_staff_logged_in():

        selected_page = st.radio(
            "Navigation",
            [
                "Customer Ordering",
                "Manager Dashboard",
            ],
            index=(
                0
                if st.session_state.current_page
                == "Customer Ordering"
                else 1
            ),
        )

    else:

        selected_page = st.radio(
            "Navigation",
            [
                "Customer Ordering",
                "Staff Login",
            ],
            index=(
                0
                if st.session_state.current_page
                == "Customer Ordering"
                else 1
            ),
        )

    st.session_state.current_page = (
        selected_page
    )

    st.divider()

    st.caption(
        "AI-powered restaurant ordering"
    )


# ============================================================
# ROUTING
# ============================================================

if (
    st.session_state.current_page
    == "Staff Login"
):

    render_staff_login()


elif (
    st.session_state.current_page
    == "Manager Dashboard"
):

    if is_staff_logged_in():

        render_manager_dashboard()

    else:

        st.session_state.current_page = (
            "Staff Login"
        )

        st.rerun()


else:

    # ========================================================
    # CUSTOMER EXPERIENCE
    # ========================================================

    if st.session_state.confirmed_order:

        display_confirmed_order(
            st.session_state.confirmed_order
        )

        st.divider()

        if st.button(
            "Start a New Order",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.order_engine = (
                OrderEngine()
            )

            st.session_state.age_verified = (
                False
            )

            st.session_state.confirmed_order = (
                None
            )

            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": (
                        "Welcome back to UrbanBite! 👋 "
                        "What would you like to order?"
                    ),
                }
            ]

            st.rerun()

    else:

        # ====================================================
        # CUSTOMER HEADER
        # ====================================================

        st.title(
            "🍔 OrderIQ",
            anchor=False,
        )

        st.caption(
            "Your AI-powered ordering assistant · UrbanBite"
        )

        st.divider()

        # ====================================================
        # CHATBOT
        # ====================================================

        with st.container(
            border=True
        ):

            st.header(
                "🤖 Your personal UrbanBite assistant",
                anchor=False,
            )

            st.write(
                "Order naturally. Ask questions. "
                "Explore the menu. I'll help you "
                "put together the right order."
            )

            st.write("")

            st.caption(
                "Try asking:"
            )

            prompt_1, prompt_2, prompt_3, prompt_4 = (
                st.columns(4)
            )

            with prompt_1:

                if st.button(
                    "🌱 Vegetarian options",
                    use_container_width=True,
                ):

                    user_message = (
                        "Show me vegetarian options."
                    )

                    st.session_state.messages.append(
                        {
                            "role": "user",
                            "content": user_message,
                        }
                    )

                    try:

                        response = (
                            process_user_message(
                                user_message
                            )
                        )

                    except Exception as e:

                        response = (
                            "I'm having trouble "
                            "connecting to the AI service "
                            "right now."
                        )

                        st.error(
                            str(e)
                        )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response,
                        }
                    )

                    st.rerun()

            with prompt_2:

                if st.button(
                    "🍽️ Dinner for two",
                    use_container_width=True,
                ):

                    user_message = (
                        "Suggest a dinner for two."
                    )

                    st.session_state.messages.append(
                        {
                            "role": "user",
                            "content": user_message,
                        }
                    )

                    try:

                        response = (
                            process_user_message(
                                user_message
                            )
                        )

                    except Exception as e:

                        response = (
                            "I'm having trouble "
                            "connecting to the AI service "
                            "right now."
                        )

                        st.error(
                            str(e)
                        )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response,
                        }
                    )

                    st.rerun()

            with prompt_3:

                if st.button(
                    "🍸 Explore drinks",
                    use_container_width=True,
                ):

                    user_message = (
                        "Show me your drinks."
                    )

                    st.session_state.messages.append(
                        {
                            "role": "user",
                            "content": user_message,
                        }
                    )

                    try:

                        response = (
                            process_user_message(
                                user_message
                            )
                        )

                    except Exception as e:

                        response = (
                            "I'm having trouble "
                            "connecting to the AI service "
                            "right now."
                        )

                        st.error(
                            str(e)
                        )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response,
                        }
                    )

                    st.rerun()

            with prompt_4:

                if st.button(
                    "💰 Under ₹500",
                    use_container_width=True,
                ):

                    user_message = (
                        "Show me good options under ₹500."
                    )

                    st.session_state.messages.append(
                        {
                            "role": "user",
                            "content": user_message,
                        }
                    )

                    try:

                        response = (
                            process_user_message(
                                user_message
                            )
                        )

                    except Exception as e:

                        response = (
                            "I'm having trouble "
                            "connecting to the AI service "
                            "right now."
                        )

                        st.error(
                            str(e)
                        )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response,
                        }
                    )

                    st.rerun()

            st.divider()

            # =================================================
            # CHAT HISTORY
            # =================================================

            chat_history = st.container(
                height=330
            )

            with chat_history:

                for message in (
                    st.session_state.messages
                ):

                    with st.chat_message(
                        message["role"]
                    ):

                        st.write(
                            message["content"]
                        )

            # =================================================
            # CHAT INPUT
            # =================================================

            user_input = st.chat_input(
                "Tell me what you'd like to eat or drink..."
            )

            if user_input:

                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": user_input,
                    }
                )

                try:

                    response = (
                        process_user_message(
                            user_input
                        )
                    )

                except Exception:

                    response = (
                        "I'm having trouble "
                        "connecting to the AI service "
                        "right now. Please try again."
                    )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response,
                    }
                )

                st.rerun()

        # ====================================================
        # MENU AT A GLANCE
        # ====================================================

        st.write("")

        st.subheader(
            "✨ Menu at a glance",
            anchor=False,
        )

        st.caption(
            "A quick look at what UrbanBite has to offer."
        )

        food_count = len(
            get_items_by_category(
                "Food"
            )
        )

        beverage_count = len(
            get_items_by_category(
                "Beverages"
            )
        )

        alcohol_count = len(
            get_items_by_category(
                "Alcohol"
            )
        )

        vegetarian_count = len(
            [
                item
                for item in all_items
                if item.get(
                    "vegetarian"
                ) is True
            ]
        )

        metric_1, metric_2, metric_3, metric_4 = (
            st.columns(4)
        )

        with metric_1:

            st.metric(
                "🍽️ Food",
                food_count,
            )

        with metric_2:

            st.metric(
                "🥤 Beverages",
                beverage_count,
            )

        with metric_3:

            st.metric(
                "🍸 Drinks & Bar",
                alcohol_count,
            )

        with metric_4:

            st.metric(
                "🌱 Vegetarian",
                vegetarian_count,
            )

        # ====================================================
        # FULL MENU
        # ====================================================

        st.write("")

        st.divider()

        st.subheader(
            "📖 Browse the full menu",
            anchor=False,
        )

        st.caption(
            "Prefer browsing? Explore the menu manually below."
        )

        food_tab, beverage_tab, alcohol_tab = (
            st.tabs(
                [
                    "🍽️ Food",
                    "🥤 Beverages",
                    "🍸 Alcohol",
                ]
            )
        )

        # ====================================================
        # MENU DISPLAY
        # ====================================================

        def display_menu(
            category
        ):

            items = get_items_by_category(
                category
            )

            if not items:

                st.info(
                    "No items found in this section."
                )

                return

            subcategories = sorted(
                {
                    item.get(
                        "subcategory"
                    )
                    for item in items
                    if item.get(
                        "subcategory"
                    )
                }
            )

            if subcategories:

                selected_subcategory = (
                    st.selectbox(
                        "Choose a section",
                        [
                            "All"
                        ] + subcategories,
                        key=(
                            f"subcategory_"
                            f"{category}"
                        ),
                    )
                )

            else:

                selected_subcategory = (
                    "All"
                )

            if (
                selected_subcategory
                == "All"
            ):

                filtered_items = items

            else:

                filtered_items = [
                    item
                    for item in items
                    if item.get(
                        "subcategory"
                    )
                    == selected_subcategory
                ]

            st.caption(
                f"{len(filtered_items)} items"
            )

            with st.container(
                height=600,
                border=True,
            ):

                for item in filtered_items:

                    name = item.get(
                        "name",
                        "Unnamed item",
                    )

                    description = item.get(
                        "description",
                        "",
                    )

                    base_price = item.get(
                        "base_price"
                    )

                    variants = item.get(
                        "variants",
                        [],
                    )

                    vegetarian = item.get(
                        "vegetarian"
                    )

                    st.subheader(
                        name,
                        anchor=False,
                    )

                    if description:

                        st.write(
                            description
                        )

                    tags = []

                    if vegetarian is True:

                        tags.append(
                            "🌱 Vegetarian"
                        )

                    elif vegetarian is False:

                        tags.append(
                            "🍗 Non-Vegetarian"
                        )

                    if item.get(
                        "alcoholic"
                    ):

                        tags.append(
                            "🍸 Alcoholic"
                        )

                    if tags:

                        st.caption(
                            " · ".join(
                                tags
                            )
                        )

                    if variants:

                        variant_names = [
                            v.get(
                                "name"
                            )
                            for v in variants
                            if v.get(
                                "name"
                            )
                        ]

                        selected_variant = (
                            st.selectbox(
                                "Size / variant",
                                variant_names,
                                key=(
                                    f"variant_"
                                    f"{category}_"
                                    f"{item['id']}"
                                ),
                            )
                        )

                        selected_price = next(
                            (
                                v.get(
                                    "price"
                                )
                                for v in variants
                                if v.get(
                                    "name"
                                )
                                == selected_variant
                            ),
                            base_price,
                        )

                    else:

                        selected_variant = (
                            None
                        )

                        selected_price = (
                            base_price
                        )

                    price_column, button_column = (
                        st.columns(
                            [2, 1]
                        )
                    )

                    with price_column:

                        if (
                            selected_price
                            is not None
                        ):

                            st.write(
                                f"**₹{selected_price:,.0f}**"
                            )

                    with button_column:

                        if st.button(
                            "Add to Cart",
                            key=(
                                f"add_"
                                f"{category}_"
                                f"{item['id']}"
                            ),
                            use_container_width=True,
                        ):

                            result = (
                                st.session_state
                                .order_engine
                                .add_item(
                                    item_id=item[
                                        "id"
                                    ],
                                    quantity=1,
                                    variant=(
                                        selected_variant
                                    ),
                                )
                            )

                            if result[
                                "success"
                            ]:

                                st.toast(
                                    result[
                                        "message"
                                    ]
                                )

                            else:

                                st.error(
                                    result[
                                        "message"
                                    ]
                                )

                    st.divider()

        # ====================================================
        # MENU TABS
        # ====================================================

        with food_tab:

            display_menu(
                "Food"
            )

        with beverage_tab:

            display_menu(
                "Beverages"
            )

        with alcohol_tab:

            display_menu(
                "Alcohol"
            )

        # ====================================================
        # CART
        # ====================================================

        st.divider()

        st.subheader(
            "🛒 Your Cart",
            anchor=False,
        )

        order = (
            st.session_state
            .order_engine
            .get_order_summary()
        )

        st.caption(
            f"{order['item_count']} items"
        )

        if not order["items"]:

            st.info(
                "Your cart is empty. "
                "Tell the AI assistant what you'd like!"
            )

        else:

            for (
                cart_index,
                cart_item,
            ) in enumerate(
                order["items"]
            ):

                name = cart_item[
                    "name"
                ]

                quantity = cart_item[
                    "quantity"
                ]

                unit_price = cart_item[
                    "unit_price"
                ]

                variant = cart_item.get(
                    "variant"
                )

                total = (
                    quantity
                    * unit_price
                )

                st.write(
                    f"**{quantity} × {name}**"
                )

                if variant:

                    st.caption(
                        f"{variant} · "
                        f"₹{unit_price:,.0f}"
                    )

                else:

                    st.caption(
                        f"₹{unit_price:,.0f} each"
                    )

                st.write(
                    f"Item total: "
                    f"**₹{total:,.0f}**"
                )

                if st.button(
                    "Remove",
                    key=(
                        f"remove_"
                        f"{cart_item['item_id']}_"
                        f"{cart_index}"
                    ),
                ):

                    (
                        st.session_state
                        .order_engine
                        .remove_item(
                            cart_item[
                                "item_id"
                            ],
                            cart_item.get(
                                "variant"
                            ),
                        )
                    )

                    st.rerun()

                st.divider()

            # =================================================
            # CHECKOUT
            # =================================================

            st.subheader(
                "💳 Checkout",
                anchor=False,
            )

            subtotal_col, subtotal_value = (
                st.columns(
                    [3, 1]
                )
            )

            with subtotal_col:

                st.write(
                    "Subtotal"
                )

            with subtotal_value:

                st.write(
                    f"₹{order['subtotal']:,.2f}"
                )

            tax_col, tax_value = (
                st.columns(
                    [3, 1]
                )
            )

            with tax_col:

                st.write(
                    f"GST ({order['tax_rate'] * 100:.0f}%)"
                )

            with tax_value:

                st.write(
                    f"₹{order['tax']:,.2f}"
                )

            st.divider()

            total_col, total_value = (
                st.columns(
                    [3, 1]
                )
            )

            with total_col:

                st.subheader(
                    "Total",
                    anchor=False,
                )

            with total_value:

                st.subheader(
                    f"₹{order['total']:,.2f}",
                    anchor=False,
                )

            # =================================================
            # ALCOHOL VERIFICATION
            # =================================================

            if order[
                "contains_alcohol"
            ]:

                st.warning(
                    "🍸 Your order contains alcohol. "
                    "You must confirm that you are 25 years "
                    "or older before placing the order."
                )

                st.session_state.age_verified = (
                    st.checkbox(
                        "I confirm that I am 25 years or older.",
                        value=(
                            st.session_state
                            .age_verified
                        ),
                    )
                )

            # =================================================
            # CONFIRM ORDER
            # =================================================

            if st.button(
                "Confirm Order",
                type="primary",
                use_container_width=True,
            ):

                confirmation = (
                    st.session_state
                    .order_engine
                    .confirm_order(
                        age_verified=(
                            st.session_state
                            .age_verified
                        )
                    )
                )

                if confirmation[
                    "success"
                ]:

                    st.session_state.confirmed_order = (
                        confirmation[
                            "order"
                        ]
                    )

                    st.session_state.order_engine = (
                        OrderEngine()
                    )

                    st.session_state.age_verified = (
                        False
                    )

                    st.rerun()

                else:

                    st.error(
                        confirmation[
                            "message"
                        ]
                    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "OrderIQ · AI-powered restaurant ordering "
    "experience for UrbanBite"
)