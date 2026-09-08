# Import the libraries we need
import os
from datetime import date, datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

# Load the variables from the .env file
load_dotenv()


# Get our Supabase connection information
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# Check that the connection information exists
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase connection information is missing.")
    st.stop()


# Connect to Supabase
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# Configure the Streamlit page
st.set_page_config(
    page_title="Blood Pressure Tracker",
    page_icon="❤️",
    layout="centered"
)


# ---------------------------------------------------------
# RESTORE LOGIN SESSION
# ---------------------------------------------------------

# Get the saved session
session = st.session_state.get("session")


# Restore the Supabase authentication session after reruns
if session is not None:

    try:
        supabase.auth.set_session(
            session.access_token,
            session.refresh_token
        )

    except Exception:
        # Clear an invalid/expired session
        st.session_state.pop("session", None)
        session = None


# ---------------------------------------------------------
# LOGIN SCREEN
# ---------------------------------------------------------

# Only show the login screen when nobody is logged in
if session is None:

    # Display the application title
    st.title("Blood Pressure Tracker")

    # Display a simple login heading
    st.subheader("Login")

    # Ask for the user's email
    email = st.text_input(
        "Email"
    )

    # Ask for the user's password
    password = st.text_input(
        "Password",
        type="password"
    )

    # Create the login button
    if st.button(
        "Log In",
        type="primary",
        use_container_width=True
    ):

        # Make sure both fields were entered
        if not email or not password:

            st.error(
                "Please enter your email and password."
            )

        else:

            try:

                # Attempt to authenticate the user
                response = supabase.auth.sign_in_with_password(
                    {
                        "email": email,
                        "password": password
                    }
                )

                # Save the successful session
                st.session_state.session = response.session

                # Refresh the app
                st.rerun()

            except Exception:

                # Display a simple login error
                st.error(
                    "Login failed. Please check your email and password."
                )


# ---------------------------------------------------------
# MAIN APPLICATION
# ---------------------------------------------------------

else:

    # Get the logged-in user's ID
    user_id = session.user.id


    # Display the application title
    st.title("Blood Pressure Tracker")


    # Display the logout button
    if st.button(
        "Log Out",
        use_container_width=True
    ):

        # Sign out of Supabase
        supabase.auth.sign_out()

        # Clear the local session
        st.session_state.pop("session", None)

        # Refresh the app
        st.rerun()


    # Add a divider
    st.divider()


    # -----------------------------------------------------
    # NAVIGATION
    # -----------------------------------------------------

    # Create the main navigation tabs
    tab_add, tab_history, tab_dashboard = st.tabs(
        [
            "Add Reading",
            "History",
            "Dashboard"
        ]
    )


   # -----------------------------------------------------
# ADD READING TAB
# -----------------------------------------------------

    with tab_add:

        # Display the section heading
        st.subheader("Add Blood Pressure Reading")

        # Put the three main measurements side by side
        col1, col2, col3 = st.columns(3)

    with col1:
        # Enter systolic pressure
        systolic = st.number_input(
            "Systolic",
            min_value=50,
            max_value=300,
            value=120,
            step=1
        )

    with col2:
        # Enter diastolic pressure
        diastolic = st.number_input(
            "Diastolic",
            min_value=30,
            max_value=200,
            value=80,
            step=1
        )

    with col3:
        # Enter pulse
        pulse = st.number_input(
            "Pulse",
            min_value=30,
            max_value=250,
            value=70,
            step=1
        )

    # Add some spacing
    st.write("")

    # Remember the last period selected
    if "last_period" not in st.session_state:
        st.session_state.last_period = "AM"

    # Select the reading period
    period = st.radio(
        "Reading Period",
        ["AM", "PM", "Pre-bed"],
        index=["AM", "PM", "Pre-bed"].index(
            st.session_state.last_period
        ),
        horizontal=True
    )

    # Remember the current selection
    st.session_state.last_period = period

    # Use today's date automatically
    reading_date = st.date_input(
        "Reading Date",
        value=date.today()
    )

    # Use the current time automatically
    reading_time = st.time_input(
        "Reading Time",
        value=datetime.now().time().replace(second=0, microsecond=0)
    )

    # Optional notes
    notes = st.text_area(
        "Notes",
        placeholder="Optional notes..."
    )

    # Save the reading
    if st.button(
        "Save Reading",
        type="primary",
        width="stretch"
    ):

        try:

            # Build the record to send to Supabase
            reading = {
                "user_id": user_id,
                "reading_date": reading_date.isoformat(),
                "reading_time": reading_time.strftime("%H:%M:%S"),
                "systolic": int(systolic),
                "diastolic": int(diastolic),
                "pulse": int(pulse),
                "period": period,
                "notes": notes.strip() if notes else None
            }

            # Insert the reading into Supabase
            supabase.table("readings").insert(
                reading
            ).execute()

            # Tell the user the reading was saved
            st.success("Reading saved successfully.")

            # Refresh the app so the new reading appears immediately
            st.rerun()

        except Exception as e:

            # Display any database error
            st.error(
                f"Could not save reading: {e}"
            )

    # -----------------------------------------------------
    # HISTORY TAB
    # -----------------------------------------------------

    with tab_history:

        # Display the history heading
        st.subheader("Reading History")


        try:

            # Get this user's readings
            history_response = (
                supabase
                .table("readings")
                .select(
                    "id, reading_date, reading_time, "
                    "systolic, diastolic, pulse, period, notes"
                )
                .eq("user_id", user_id)
                .order(
                    "reading_date",
                    desc=True
                )
                .order(
                    "reading_time",
                    desc=True
                )
                .execute()
            )


            # Get the returned data
            readings = history_response.data


            # Display the readings when they exist
            if readings:

                # Convert the readings into a DataFrame
                history_df = pd.DataFrame(
                    readings
                )


                # Rename columns for display
                history_df = history_df.rename(
                    columns={
                        "reading_date": "Date",
                        "reading_time": "Time",
                        "systolic": "Systolic",
                        "diastolic": "Diastolic",
                        "pulse": "Pulse",
                        "period": "Period",
                        "notes": "Notes"
                    }
                )


                # Drop the internal database ID
                if "id" in history_df.columns:
                    history_df = history_df.drop(
                        columns=["id"]
                    )


                # Display the history table
                st.dataframe(
                    history_df,
                    width="stretch",
                    hide_index=True
                )


            else:

                # Tell the user that no readings exist
                st.info(
                    "No readings have been recorded yet."
                )


        except Exception as e:

            # Display any history error
            st.error(
                f"Could not load reading history: {e}"
            )


    # -----------------------------------------------------
    # DASHBOARD TAB
    # -----------------------------------------------------

    with tab_dashboard:

        # Display the dashboard heading
        st.subheader("Dashboard")


        # Load the user's readings for future dashboard work
        try:

            # Get all readings for this user
            dashboard_response = (
                supabase
                .table("readings")
                .select(
                    "reading_date, reading_time, "
                    "systolic, diastolic, pulse"
                )
                .eq("user_id", user_id)
                .order(
                    "reading_date"
                )
                .order(
                    "reading_time"
                )
                .execute()
            )


            # Convert the results into a DataFrame
            dashboard_df = pd.DataFrame(
                dashboard_response.data
            )


            # Display the number of readings
            st.metric(
                "Total Readings",
                len(dashboard_df)
            )


            # Show a placeholder until we build the dashboard
            st.info(
                "Dashboard analysis will be added next."
            )


        except Exception as e:

            # Display any dashboard error
            st.error(
                f"Could not load dashboard data: {e}"
            )