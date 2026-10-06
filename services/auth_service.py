import hashlib
import streamlit as st


# ============================================================
# DEMO STAFF CREDENTIALS
# ============================================================

STAFF_USERNAME = "manager"
STAFF_PASSWORD_HASH = hashlib.sha256(
    "UrbanBite@2026".encode("utf-8")
).hexdigest()


# ============================================================
# PASSWORD VERIFICATION
# ============================================================

def verify_staff_credentials(
    username,
    password,
):

    username = username.strip()


    password_hash = hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


    return (
        username == STAFF_USERNAME
        and password_hash == STAFF_PASSWORD_HASH
    )


# ============================================================
# LOGIN STATE
# ============================================================

def is_staff_logged_in():

    return st.session_state.get(
        "staff_logged_in",
        False,
    )


# ============================================================
# LOG IN
# ============================================================

def login_staff(
    username,
    password,
):

    if verify_staff_credentials(
        username,
        password,
    ):

        st.session_state.staff_logged_in = True

        st.session_state.staff_username = (
            username.strip()
        )

        return True


    return False


# ============================================================
# LOG OUT
# ============================================================

def logout_staff():

    st.session_state.staff_logged_in = False

    st.session_state.staff_username = ""


# ============================================================
# GET CURRENT STAFF USER
# ============================================================

def get_current_staff():

    return st.session_state.get(
        "staff_username",
        "",
    )