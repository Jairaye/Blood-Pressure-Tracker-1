# Import the libraries we need
import os
from datetime import date, datetime, time

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

# Load the variables from the .env file
load_dotenv()

# Get our Supabase connection information
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Make sure the connection information exists
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase connection information is missing from the .env file.")
    st.stop()

# Connect to Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Restore the logged-in Supabase session after each Streamlit rerun
session = st.session_state.get("session")

if session is not None:
    supabase.auth.set_session(
        session.access_token,
        session.refresh_token
    )

# Set up the Streamlit page
st.set_page_config(
    page_title="Blood Pressure Tracker",
    page_icon="❤️",
    layout="centered"
)

# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

# Get the current session
session = st.session_state.get("session")

# Show the login screen if the user is not logged in
if session is None:

    # Display the application title
    st.title("Blood Pressure Tracker")

    # Display the login heading
    st.subheader("Login")

    # Ask for the user's email
    email = st.text_input("Email")

    # Ask for the user's password
    password = st.text_input("Password", type="password")

    # Create the login button
    if st.button("Log In"):

        # Make sure both fields were entered
        if not email or not password:
            st.error("Please enter your email and password.")

        else:
            try:
                # Attempt to log the user into Supabase
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
                # Show a simple login error
                st.error("Login failed. Please check the email and password.")

# ---------------------------------------------------------
# BLOOD PRESSURE TRACKER
# ---------------------------------------------------------

else:

    # Get the logged-in user's ID
    user_id = session.user.id

    # Display the application title
    st.title("Blood Pressure Tracker")

    # Display a logout button
    if st.button("Log Out"):
        # Sign out of Supabase
        supabase.auth.sign_out()

        # Remove the saved session
        st.session_state.pop("session", None)

        # Refresh the application
        st.rerun()

    # Add a divider
    st.divider()

    # Display the Add Reading heading
    st.subheader("Add Blood Pressure Reading")

    # Create the blood pressure input fields
    systolic = st.number_input(
        "Systolic",
        min_value=50,
        max_value=300,
        value=120,
        step=1
    )

    diastolic = st.number_input(
        "Diastolic",
        min_value=30,
        max_value=200,
        value=80,
        step=1
    )

    pulse = st.number_input(
        "Pulse",
        min_value=30,
        max_value=250,
        value=70,
        step=1
    )

    # Let the user select AM, PM, or Pre-bed
    period = st.selectbox(
        "Reading Period",
        [
            "AM",
            "PM",
            "Pre-bed"
        ]
    )

    # Date of the reading
    reading_date = st.date_input(
        "Reading Date",
        value=date.today()
    )

    # Time of the reading
    reading_time = st.time_input(
        "Reading Time",
        value=datetime.now().time()
    )

    # Optional notes
    notes = st.text_area(
        "Notes",
        placeholder="Optional notes about this reading..."
    )

    # Save the reading
    if st.button("Save Reading", type="primary"):

        try:

            # Build the reading we are going to send to Supabase
            reading = {
                "user_id": user_id,
                "reading_date": reading_date.isoformat(),
                "reading_time": reading_time.strftime("%H:%M:%S"),
                "systolic": int(systolic),
                "diastolic": int(diastolic),
                "pulse": int(pulse),
                "period": period,
                "notes": notes
            }

            # Insert the reading into the database
            response = supabase.table("readings").insert(reading).execute()

            # Tell the user the reading was saved
            st.success("Reading saved successfully.")

        except Exception as e:

            # Display the error if something went wrong
            st.error(f"Could not save reading: {e}")

# ---------------------------------------------------------
# READING HISTORY
# ---------------------------------------------------------

# Add a divider
st.divider()

# Display the history heading
st.subheader("Reading History")

try:
    # Retrieve this user's readings from Supabase
    history_response = (
        supabase
        .table("readings")
        .select(
            "id, reading_date, reading_time, systolic, diastolic, "
            "pulse, period, notes"
        )
        .eq("user_id", user_id)
        .order("reading_date", desc=True)
        .order("reading_time", desc=True)
        .execute()
    )

    # Convert the results into a list
    readings = history_response.data

    # Display the readings if any exist
    if readings:
        st.dataframe(
            readings,
            use_container_width=True,
            hide_index=True
        )

    else:
        # Tell the user if there are no readings yet
        st.info("No readings have been recorded yet.")

except Exception as e:

    # Display an error if the history could not be loaded
    st.error(f"Could not load reading history: {e}")