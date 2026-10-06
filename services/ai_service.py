import json
import re

import streamlit as st
from groq import Groq


MODEL_NAME = "openai/gpt-oss-20b"


# ============================================================
# GROQ CLIENT
# ============================================================

def get_groq_client():
    api_key = st.secrets["GROQ_API_KEY"]

    return Groq(
        api_key=api_key
    )


# ============================================================
# BUILD CATALOG CONTEXT
# ============================================================

def build_catalog_context(relevant_items):
    """
    Convert the retrieved catalog items into compact text
    that the AI can use.

    The AI can only select products that appear here.
    """

    if not relevant_items:
        return "No matching catalog items were found."

    lines = []

    for item in relevant_items:

        item_id = item.get("id")

        name = item.get(
            "name",
            ""
        )

        category = item.get(
            "category",
            ""
        )

        subcategory = item.get(
            "subcategory",
            ""
        )

        description = item.get(
            "description",
            ""
        )

        alcoholic = item.get(
            "alcoholic",
            False
        )

        base_price = item.get(
            "base_price"
        )

        variants = item.get(
            "variants",
            []
        )

        variant_text = ""

        if variants:

            variant_parts = []

            for variant in variants:

                variant_name = variant.get(
                    "name"
                )

                variant_price = variant.get(
                    "price"
                )

                variant_parts.append(
                    f"{variant_name}: ₹{variant_price}"
                )

            variant_text = (
                " | Variants: "
                + ", ".join(variant_parts)
            )

        lines.append(
            f"ID: {item_id} | "
            f"Name: {name} | "
            f"Category: {category} | "
            f"Subcategory: {subcategory} | "
            f"Price: {base_price} | "
            f"Alcoholic: {alcoholic}"
            f"{variant_text} | "
            f"Description: {description}"
        )

    return "\n".join(lines)


# ============================================================
# EXTRACT JSON FROM MODEL RESPONSE
# ============================================================

def extract_json(response_text):
    """
    Safely extract a JSON object from the model response.

    Handles cases where the model accidentally wraps JSON
    inside markdown code fences.
    """

    if not response_text:
        return None

    text = response_text.strip()

    # Remove markdown code fences
    text = re.sub(
        r"^```(?:json)?",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"```$",
        "",
        text,
    )

    text = text.strip()

    # First attempt: entire response
    try:

        return json.loads(text)

    except json.JSONDecodeError:
        pass


    # Second attempt: find first JSON object
    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL,
    )

    if match:

        try:

            return json.loads(
                match.group(0)
            )

        except json.JSONDecodeError:
            pass


    return None


# ============================================================
# AI AGENT
# ============================================================

def get_ai_action(
    user_message,
    relevant_items=None,
    conversation_history=None,
):
    """
    Ask Groq to interpret the user's request.

    Returns a structured dictionary:

    {
        "action": "...",
        "item_name": "...",
        "item_id": "...",
        "quantity": 1,
        "variant": null,
        "response": "..."
    }
    """

    client = get_groq_client()


    catalog_context = build_catalog_context(
        relevant_items or []
    )


    system_prompt = """
You are OrderIQ, the AI ordering agent for UrbanBite.

You help restaurant customers discover menu items and manage
their order.

You MUST return ONLY valid JSON.

Do not return markdown.
Do not return explanations outside the JSON object.


============================================================
AVAILABLE ACTIONS
============================================================

You must choose exactly ONE of these actions:

1. ADD_ITEM

Use when the customer wants to add something to their order.

Examples:
"Add two Old Fashioneds"
"I'll have a Margarita"
"Put one Paneer Tikka in my cart"


2. REMOVE_ITEM

Use when the customer wants to remove something from their order.

Examples:
"Remove the Margarita"
"Take the fries out"
"Remove one Old Fashioned"


3. UPDATE_QUANTITY

Use when the customer wants to change the quantity.

Examples:
"Make that three Old Fashioneds"
"Change the Paneer Tikka to two"
"I want four instead"


4. SEARCH_MENU

Use when the customer is asking about available menu items.

Examples:
"Show me cocktails"
"What vegetarian starters do you have?"
"What pizzas are available?"
"Show me drinks under 500"


5. CHAT

Use for general conversation, recommendations, greetings,
clarifications, or anything that does not directly require
a cart action or menu search.


============================================================
CRITICAL CATALOG RULES
============================================================

You may ONLY select an item that exists in the supplied
catalog context.

NEVER invent an item.

NEVER invent a price.

NEVER invent an item ID.

If the requested item cannot be confidently matched to a
catalog item, use:

"action": "CHAT"

and explain that you could not confidently identify the item.

For ADD_ITEM, REMOVE_ITEM and UPDATE_QUANTITY:

- item_id must come from the catalog.
- item_name must come from the catalog.
- quantity must be a positive integer.
- variant must be one of the supplied variants or null.


============================================================
ALCOHOL RULE
============================================================

Alcoholic items may be added to the order.

Do NOT reject an alcoholic item simply because it is alcoholic.

The Python checkout system will handle age verification.

You should simply identify the alcoholic menu item correctly.


============================================================
RESPONSE FORMAT
============================================================

Always return exactly this structure:

{
    "action": "ADD_ITEM",
    "item_id": "CK004",
    "item_name": "Old Fashioned",
    "quantity": 2,
    "variant": null,
    "response": "Absolutely — I've added 2 Old Fashioneds to your order."
}

For SEARCH_MENU:

{
    "action": "SEARCH_MENU",
    "item_id": null,
    "item_name": null,
    "quantity": 1,
    "variant": null,
    "response": "Here are some cocktails available at UrbanBite."
}

For CHAT:

{
    "action": "CHAT",
    "item_id": null,
    "item_name": null,
    "quantity": 1,
    "variant": null,
    "response": "I'd be happy to help you choose something."
}


============================================================
IMPORTANT
============================================================

The "response" field should be short and customer-friendly.

Do not say an item was added unless the requested action
is ADD_ITEM.

Do not say an item was removed unless the requested action
is REMOVE_ITEM.

Do not claim that an order was placed.

The Python OrderEngine will actually execute cart actions.

You are interpreting the request, not executing it.
"""


    system_prompt += (
        "\n\n============================================================\n"
        "CURRENT URBANBITE CATALOG CONTEXT\n"
        "============================================================\n\n"
        + catalog_context
    )


    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]


    # --------------------------------------------------------
    # CONVERSATION HISTORY
    # --------------------------------------------------------

    if conversation_history:

        for message in conversation_history[-10:]:

            messages.append(
                {
                    "role": message["role"],
                    "content": message["content"],
                }
            )


    # --------------------------------------------------------
    # CURRENT USER REQUEST
    # --------------------------------------------------------

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )


    # --------------------------------------------------------
    # CALL GROQ
    # --------------------------------------------------------

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0,
    )


    raw_response = (
        response
        .choices[0]
        .message
        .content
    )


    parsed_response = extract_json(
        raw_response
    )


    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not parsed_response:

        return {
            "action": "CHAT",
            "item_id": None,
            "item_name": None,
            "quantity": 1,
            "variant": None,
            "response": (
                "I'm sorry, I couldn't process that request. "
                "Could you try saying it another way?"
            ),
        }


    # --------------------------------------------------------
    # VALIDATE ACTION
    # --------------------------------------------------------

    valid_actions = {
        "ADD_ITEM",
        "REMOVE_ITEM",
        "UPDATE_QUANTITY",
        "SEARCH_MENU",
        "CHAT",
    }


    action = parsed_response.get(
        "action",
        "CHAT",
    )


    if action not in valid_actions:

        action = "CHAT"


    # --------------------------------------------------------
    # NORMALIZE RESULT
    # --------------------------------------------------------

    quantity = parsed_response.get(
        "quantity",
        1,
    )


    try:

        quantity = int(quantity)

    except (TypeError, ValueError):

        quantity = 1


    if quantity < 1:

        quantity = 1


    return {
        "action": action,

        "item_id": parsed_response.get(
            "item_id"
        ),

        "item_name": parsed_response.get(
            "item_name"
        ),

        "quantity": quantity,

        "variant": parsed_response.get(
            "variant"
        ),

        "response": parsed_response.get(
            "response",
            "How can I help you?",
        ),
    }


# ============================================================
# BACKWARD-COMPATIBLE CHAT FUNCTION
# ============================================================

def get_ai_response(
    user_message,
    relevant_items=None,
    conversation_history=None,
):
    """
    Existing chatbot interface.

    This keeps the previous function working while the new
    agent layer is introduced.
    """

    result = get_ai_action(
        user_message=user_message,
        relevant_items=relevant_items,
        conversation_history=conversation_history,
    )

    return result["response"]


# ============================================================
# TEST FUNCTION
# ============================================================

def test_groq():

    client = get_groq_client()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are OrderIQ, an AI restaurant "
                    "ordering assistant."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Say hello to OrderIQ in one "
                    "short sentence."
                ),
            },
        ],
        temperature=0,
    )

    return response.choices[0].message.content
