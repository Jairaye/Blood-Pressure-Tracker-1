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

# Get the saved login session
session = st.session_state.get("session")


# Restore the Supabase authentication session after reruns
if session is not None:

    try:

        supabase.auth.set_session(
            session.access_token,
            session.refresh_token
        )

    except Exception:

        # Clear an invalid or expired session
        st.session_state.pop(
            "session",
            None
        )

        session = None


# ---------------------------------------------------------
# LOGIN SCREEN
# ---------------------------------------------------------

# Only show this section when the user is not logged in
if session is None:

    # Display the application title
    st.title("Blood Pressure Tracker")

    # Display the login heading
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
        width="stretch"
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

                # Refresh the application
                st.rerun()

            except Exception:

                # Display a simple login error
                st.error(
                    "Login failed. Please check the email and password."
                )


# ---------------------------------------------------------
# MAIN APPLICATION
# ---------------------------------------------------------

else:

    # Get the logged-in user's ID
    user_id = session.user.id


    # -----------------------------------------------------
    # APPLICATION HEADER
    # -----------------------------------------------------

    # Display the application title
    st.title("Blood Pressure Tracker")


    # Create the logout button
    if st.button(
        "Log Out",
        width="stretch"
    ):

        # Sign out of Supabase
        supabase.auth.sign_out()

        # Remove the saved session
        st.session_state.pop(
            "session",
            None
        )

        # Refresh the application
        st.rerun()


    # Add a divider below the header
    st.divider()


    # -----------------------------------------------------
    # NAVIGATION
    # -----------------------------------------------------

    # Create the main application tabs
    tab_add, tab_history, tab_dashboard = st.tabs(
        [
            "Add Reading",
            "History",
            "Dashboard"
        ]
    )


    # =====================================================
    # ADD READING TAB
    # =====================================================

    with tab_add:

        # Display the section heading
        st.subheader(
            "Add Blood Pressure Reading"
        )


        # Put the three main measurements side by side
        col1, col2, col3 = st.columns(3)


        # Systolic input
        with col1:

            systolic = st.number_input(
                "Systolic",
                min_value=50,
                max_value=300,
                value=120,
                step=1
            )


        # Diastolic input
        with col2:

            diastolic = st.number_input(
                "Diastolic",
                min_value=30,
                max_value=200,
                value=80,
                step=1
            )


        # Pulse input
        with col3:

            pulse = st.number_input(
                "Pulse",
                min_value=30,
                max_value=250,
                value=70,
                step=1
            )


        # Add some spacing
        st.write("")


        # -------------------------------------------------
        # READING PERIOD
        # -------------------------------------------------

        # Remember the last period selected
        if "last_period" not in st.session_state:

            st.session_state.last_period = "AM"


        # Reading period selector
        period = st.radio(
            "Reading Period",
            [
                "AM",
                "PM",
                "Pre-bed"
            ],
            index=[
                "AM",
                "PM",
                "Pre-bed"
            ].index(
                st.session_state.last_period
            ),
            horizontal=True
        )


        # Remember the current selection
        st.session_state.last_period = period


        # -------------------------------------------------
        # DATE AND TIME
        # -------------------------------------------------

        # Use today's date automatically
        reading_date = st.date_input(
            "Reading Date",
            value=date.today()
        )


        # Use the current time automatically
        reading_time = st.time_input(
            "Reading Time",
            value=datetime.now().time().replace(
                second=0,
                microsecond=0
            )
        )


        # -------------------------------------------------
        # NOTES
        # -------------------------------------------------

        # Optional notes
        notes = st.text_area(
            "Notes",
            placeholder="Optional notes..."
        )


        # -------------------------------------------------
        # SAVE READING
        # -------------------------------------------------

        # Create the save button
        if st.button(
            "Save Reading",
            type="primary",
            width="stretch"
        ):

            try:

                # Build the reading record
                reading = {
                    "user_id": user_id,
                    "reading_date": reading_date.isoformat(),
                    "reading_time": reading_time.strftime(
                        "%H:%M:%S"
                    ),
                    "systolic": int(systolic),
                    "diastolic": int(diastolic),
                    "pulse": int(pulse),
                    "period": period,
                    "notes": notes.strip() if notes else None
                }


                # Insert the reading into Supabase
                supabase.table(
                    "readings"
                ).insert(
                    reading
                ).execute()


                # Show a success message
                st.success(
                    "Reading saved successfully."
                )


                # Refresh the application
                st.rerun()


            except Exception as e:

                # Display any database error
                st.error(
                    f"Could not save reading: {e}"
                )


    # =====================================================
    # HISTORY TAB
    # =====================================================

    with tab_history:

        # Display the history heading
        st.subheader(
            "Reading History"
        )


        # -------------------------------------------------
        # CHECK FOR ACTIVE EDIT
        # -------------------------------------------------

        if "editing_reading" in st.session_state:

            # Get the reading currently being edited
            editing_reading = st.session_state.editing_reading


            # Display the editing heading
            st.markdown(
                "### Edit Reading"
            )


            # Create the edit form
            with st.form(
                "edit_reading_form"
            ):

                # Create the three measurement columns
                edit_col1, edit_col2, edit_col3 = st.columns(3)


                # Systolic
                with edit_col1:

                    edit_systolic = st.number_input(
                        "Systolic",
                        min_value=50,
                        max_value=300,
                        value=int(
                            editing_reading["systolic"]
                        ),
                        step=1,
                        key="edit_systolic"
                    )


                # Diastolic
                with edit_col2:

                    edit_diastolic = st.number_input(
                        "Diastolic",
                        min_value=30,
                        max_value=200,
                        value=int(
                            editing_reading["diastolic"]
                        ),
                        step=1,
                        key="edit_diastolic"
                    )


                # Pulse
                with edit_col3:

                    edit_pulse = st.number_input(
                        "Pulse",
                        min_value=30,
                        max_value=250,
                        value=int(
                            editing_reading["pulse"]
                        ) if editing_reading["pulse"] is not None else 70,
                        step=1,
                        key="edit_pulse"
                    )


                # Get the current period
                current_period = editing_reading["period"]


                # Find the correct index
                if current_period in [
                    "AM",
                    "PM",
                    "Pre-bed"
                ]:

                    period_index = [
                        "AM",
                        "PM",
                        "Pre-bed"
                    ].index(
                        current_period
                    )

                else:

                    period_index = 0


                # Edit period
                edit_period = st.selectbox(
                    "Reading Period",
                    [
                        "AM",
                        "PM",
                        "Pre-bed"
                    ],
                    index=period_index,
                    key="edit_period"
                )


                # Edit date
                edit_date = st.date_input(
                    "Reading Date",
                    value=pd.to_datetime(
                        editing_reading["reading_date"]
                    ).date(),
                    key="edit_date"
                )


                # Handle existing time
                if editing_reading["reading_time"]:

                    existing_time_text = (
                        editing_reading["reading_time"]
                    )

                    existing_time = datetime.strptime(
                        existing_time_text,
                        "%H:%M:%S"
                    ).time()

                else:

                    existing_time = datetime.now().time().replace(
                        second=0,
                        microsecond=0
                    )


                # Edit time
                edit_time = st.time_input(
                    "Reading Time",
                    value=existing_time,
                    key="edit_time"
                )


                # Edit notes
                edit_notes = st.text_area(
                    "Notes",
                    value=editing_reading["notes"] or "",
                    key="edit_notes"
                )


                # Create the form buttons
                save_edit, cancel_edit = st.columns(2)


                with save_edit:

                    # Save the edited reading
                    save_edit_button = st.form_submit_button(
                        "Save Changes",
                        type="primary",
                        width="stretch"
                    )


                with cancel_edit:

                    # Cancel the edit
                    cancel_edit_button = st.form_submit_button(
                        "Cancel",
                        width="stretch"
                    )


                # Handle the Save Changes button
                if save_edit_button:

                    try:

                        # Create the updated reading
                        updated_reading = {
                            "reading_date": edit_date.isoformat(),
                            "reading_time": edit_time.strftime(
                                "%H:%M:%S"
                            ),
                            "systolic": int(edit_systolic),
                            "diastolic": int(edit_diastolic),
                            "pulse": int(edit_pulse),
                            "period": edit_period,
                            "notes": edit_notes.strip() if edit_notes else None
                        }


                        # Update only this user's reading
                        supabase.table(
                            "readings"
                        ).update(
                            updated_reading
                        ).eq(
                            "id",
                            editing_reading["id"]
                        ).eq(
                            "user_id",
                            user_id
                        ).execute()


                        # Remove the active edit
                        st.session_state.pop(
                            "editing_reading",
                            None
                        )


                        # Show success message
                        st.success(
                            "Reading updated successfully."
                        )


                        # Refresh the app
                        st.rerun()


                    except Exception as e:

                        # Display the update error
                        st.error(
                            f"Could not update reading: {e}"
                        )


                # Handle the Cancel button
                if cancel_edit_button:

                    # Remove the active edit
                    st.session_state.pop(
                        "editing_reading",
                        None
                    )


                    # Refresh the application
                    st.rerun()


            # Divider between edit form and history
            st.divider()


        # -------------------------------------------------
        # CHECK FOR DELETE CONFIRMATION
        # -------------------------------------------------

        if "deleting_reading" in st.session_state:

            # Get the reading awaiting deletion
            deleting_reading = st.session_state.deleting_reading


            # Display the confirmation message
            st.warning(
                f'Are you sure you want to delete '
                f'{deleting_reading["systolic"]}/'
                f'{deleting_reading["diastolic"]} '
                f'from {deleting_reading["reading_date"]}?'
            )


            # Create the confirmation buttons
            confirm_col, cancel_col = st.columns(2)


            with confirm_col:

                # Confirm the deletion
                if st.button(
                    "Yes, Delete",
                    type="primary",
                    width="stretch",
                    key="confirm_delete"
                ):

                    try:

                        # Delete only this user's selected reading
                        supabase.table(
                            "readings"
                        ).delete().eq(
                            "id",
                            deleting_reading["id"]
                        ).eq(
                            "user_id",
                            user_id
                        ).execute()


                        # Clear the pending deletion
                        st.session_state.pop(
                            "deleting_reading",
                            None
                        )


                        # Show success message
                        st.success(
                            "Reading deleted successfully."
                        )


                        # Refresh the app
                        st.rerun()


                    except Exception as e:

                        # Display any deletion error
                        st.error(
                            f"Could not delete reading: {e}"
                        )


            with cancel_col:

                # Cancel the deletion
                if st.button(
                    "Cancel",
                    width="stretch",
                    key="cancel_delete"
                ):

                    # Clear the pending deletion
                    st.session_state.pop(
                        "deleting_reading",
                        None
                    )


                    # Refresh the application
                    st.rerun()


            # Stop displaying the normal history temporarily
            st.divider()


        # -------------------------------------------------
        # LOAD HISTORY
        # -------------------------------------------------

        try:

            # Get this user's readings
            history_response = (
                supabase
                .table("readings")
                .select(
                    "id, reading_date, reading_time, "
                    "systolic, diastolic, pulse, period, notes"
                )
                .eq(
                    "user_id",
                    user_id
                )
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


            # Get the readings
            readings = history_response.data


            # Check whether readings exist
            if readings:

                # Display each reading as an expandable item
                for reading in readings:

                    # Get the reading ID
                    reading_id = reading["id"]


                    # Build the display title
                    pulse_text = (
                        str(reading["pulse"])
                        if reading["pulse"] is not None
                        else "N/A"
                    )


                    reading_title = (
                        f'{reading["reading_date"]} — '
                        f'{reading["systolic"]}/'
                        f'{reading["diastolic"]} '
                        f'({pulse_text} bpm)'
                    )


                    # Create an expandable reading section
                    with st.expander(
                        reading_title
                    ):

                        # Display date
                        st.write(
                            f'**Date:** {reading["reading_date"]}'
                        )


                        # Display time when available
                        if reading["reading_time"]:

                            st.write(
                                f'**Time:** {reading["reading_time"]}'
                            )


                        # Display blood pressure
                        st.write(
                            f'**Blood Pressure:** '
                            f'{reading["systolic"]}/'
                            f'{reading["diastolic"]}'
                        )


                        # Display pulse
                        st.write(
                            f'**Pulse:** {pulse_text}'
                        )


                        # Display period
                        if reading["period"]:

                            st.write(
                                f'**Period:** {reading["period"]}'
                            )


                        # Display notes
                        if reading["notes"]:

                            st.write(
                                f'**Notes:** {reading["notes"]}'
                            )


                        # Create Edit and Delete buttons
                        edit_button_col, delete_button_col = st.columns(2)


                        # Edit button
                        with edit_button_col:

                            if st.button(
                                "Edit",
                                key=f"edit_{reading_id}",
                                width="stretch"
                            ):

                                # Store the selected reading
                                st.session_state.editing_reading = reading

                                # Make sure delete mode is cleared
                                st.session_state.pop(
                                    "deleting_reading",
                                    None
                                )

                                # Refresh the app
                                st.rerun()


                        # Delete button
                        with delete_button_col:

                            if st.button(
                                "Delete",
                                key=f"delete_{reading_id}",
                                width="stretch"
                            ):

                                # Store the selected reading
                                st.session_state.deleting_reading = reading

                                # Make sure edit mode is cleared
                                st.session_state.pop(
                                    "editing_reading",
                                    None
                                )

                                # Refresh the app
                                st.rerun()


            else:

                # Tell the user there are no readings
                st.info(
                    "No readings have been recorded yet."
                )


        except Exception as e:

            # Display any history error
            st.error(
                f"Could not load reading history: {e}"
            )


    # =====================================================
    # DASHBOARD TAB
    # =====================================================

    with tab_dashboard:

        # Display the dashboard heading
        st.subheader("Dashboard")

        try:

            # Get all readings for this user
            dashboard_response = (
                supabase
                .table("readings")
                .select(
                    "reading_date, reading_time, "
                    "systolic, diastolic, pulse, period"
                )
                .eq(
                    "user_id",
                    user_id
                )
                .order(
                    "reading_date"
                )
                .order(
                    "reading_time"
                )
                .execute()
            )

            # Convert the readings into a DataFrame
            dashboard_df = pd.DataFrame(
                dashboard_response.data
            )

            # Check whether readings exist
            if dashboard_df.empty:

                # Tell the user there is no data yet
                st.info(
                    "There are not enough readings to display the dashboard yet."
                )

            else:

                # -------------------------------------------------
                # PREPARE THE DATA
                # -------------------------------------------------

                # Convert dates into datetime values
                dashboard_df["reading_date"] = pd.to_datetime(
                    dashboard_df["reading_date"]
                )

                # Convert numeric fields to numbers
                dashboard_df["systolic"] = pd.to_numeric(
                    dashboard_df["systolic"],
                    errors="coerce"
                )

                dashboard_df["diastolic"] = pd.to_numeric(
                    dashboard_df["diastolic"],
                    errors="coerce"
                )

                dashboard_df["pulse"] = pd.to_numeric(
                    dashboard_df["pulse"],
                    errors="coerce"
                )

                # Remove rows missing the main BP measurements
                dashboard_df = dashboard_df.dropna(
                    subset=["systolic", "diastolic"]
                )

                # Get the most recent reading date
                latest_date = dashboard_df["reading_date"].max()

                # Get the oldest reading date
                earliest_date = dashboard_df["reading_date"].min()


                # -------------------------------------------------
                # TIME PERIOD FILTER
                # -------------------------------------------------

                # Create the dashboard period selector
                dashboard_period = st.radio(
                    "Time Period",
                    [
                        "7 Days",
                        "30 Days",
                        "90 Days",
                        "All Time",
                        "Custom"
                    ],
                    horizontal=True
                )


                # Set default custom dates
                custom_start = None
                custom_end = None


                # Show date selectors for Custom
                if dashboard_period == "Custom":

                    # Create two columns for the date selectors
                    start_col, end_col = st.columns(2)


                    with start_col:

                        # Select custom start date
                        custom_start = st.date_input(
                            "Start Date",
                            value=earliest_date.date(),
                            min_value=earliest_date.date(),
                            max_value=latest_date.date()
                        )


                    with end_col:

                        # Select custom end date
                        custom_end = st.date_input(
                            "End Date",
                            value=latest_date.date(),
                            min_value=earliest_date.date(),
                            max_value=latest_date.date()
                        )


                    # Make sure the dates are valid
                    if custom_start > custom_end:

                        st.error(
                            "Start Date cannot be after End Date."
                        )

                        st.stop()


                # -------------------------------------------------
                # FILTER THE DATA
                # -------------------------------------------------

                if dashboard_period == "7 Days":

                    # Calculate the beginning of the 7-day period
                    start_date = latest_date - pd.Timedelta(days=6)

                    # Filter the readings
                    filtered_df = dashboard_df[
                        dashboard_df["reading_date"] >= start_date
                    ]


                elif dashboard_period == "30 Days":

                    # Calculate the beginning of the 30-day period
                    start_date = latest_date - pd.Timedelta(days=29)

                    # Filter the readings
                    filtered_df = dashboard_df[
                        dashboard_df["reading_date"] >= start_date
                    ]


                elif dashboard_period == "90 Days":

                    # Calculate the beginning of the 90-day period
                    start_date = latest_date - pd.Timedelta(days=89)

                    # Filter the readings
                    filtered_df = dashboard_df[
                        dashboard_df["reading_date"] >= start_date
                    ]


                elif dashboard_period == "Custom":

                    # Convert the custom dates to timestamps
                    start_date = pd.Timestamp(custom_start)
                    end_date = pd.Timestamp(custom_end)

                    # Filter the readings
                    filtered_df = dashboard_df[
                        (dashboard_df["reading_date"] >= start_date)
                        & (dashboard_df["reading_date"] <= end_date)
                    ]


                else:

                    # Use all readings
                    filtered_df = dashboard_df.copy()


                # -------------------------------------------------
                # HANDLE EMPTY FILTER RESULTS
                # -------------------------------------------------

                if filtered_df.empty:

                    # Tell the user the selected range has no data
                    st.warning(
                        "There are no readings in the selected date range."
                    )

                else:

                    # -------------------------------------------------
                    # SUMMARY METRICS
                    # -------------------------------------------------

                    # Calculate average systolic
                    average_systolic = filtered_df[
                        "systolic"
                    ].mean()

                    # Calculate average diastolic
                    average_diastolic = filtered_df[
                        "diastolic"
                    ].mean()

                    # Calculate average pulse
                    average_pulse = filtered_df[
                        "pulse"
                    ].mean()

                    # Calculate minimum systolic
                    minimum_systolic = filtered_df[
                        "systolic"
                    ].min()

                    # Calculate maximum systolic
                    maximum_systolic = filtered_df[
                        "systolic"
                    ].max()

                    # Calculate minimum diastolic
                    minimum_diastolic = filtered_df[
                        "diastolic"
                    ].min()

                    # Calculate maximum diastolic
                    maximum_diastolic = filtered_df[
                        "diastolic"
                    ].max()

                    # Count the readings
                    reading_count = len(filtered_df)


                    # -------------------------------------------------
                    # TOP METRICS
                    # -------------------------------------------------

                    # First row of metrics
                    metric1, metric2 = st.columns(2)


                    with metric1:

                        # Display average blood pressure
                        st.metric(
                            "Average BP",
                            f"{average_systolic:.0f} / "
                            f"{average_diastolic:.0f}"
                        )


                    with metric2:

                        # Display average pulse
                        if pd.isna(average_pulse):

                            st.metric(
                                "Average Pulse",
                                "N/A"
                            )

                        else:

                            st.metric(
                                "Average Pulse",
                                f"{average_pulse:.0f}"
                            )


                    # Second row of metrics
                    metric3, metric4 = st.columns(2)


                    with metric3:

                        # Display total readings
                        st.metric(
                            "Readings",
                            reading_count
                        )


                    with metric4:

                        # Display most recent date in the selected range
                        selected_latest_date = (
                            filtered_df["reading_date"].max()
                        )

                        st.metric(
                            "Latest Reading",
                            selected_latest_date.strftime(
                                "%m/%d/%Y"
                            )
                        )


                    # -------------------------------------------------
                    # RANGE SUMMARY
                    # -------------------------------------------------

                    # Display the selected date range
                    selected_start = (
                        filtered_df["reading_date"].min()
                    )

                    selected_end = (
                        filtered_df["reading_date"].max()
                    )

                    st.caption(
                        f"Showing readings from "
                        f"{selected_start.strftime('%m/%d/%Y')} "
                        f"through "
                        f"{selected_end.strftime('%m/%d/%Y')}"
                    )


                    # -------------------------------------------------
                    # MINIMUM / MAXIMUM
                    # -------------------------------------------------

                    st.markdown(
                        "### Blood Pressure Range"
                    )


                    range_col1, range_col2 = st.columns(2)


                    with range_col1:

                        # Display systolic range
                        st.metric(
                            "Systolic Range",
                            f"{minimum_systolic:.0f} - "
                            f"{maximum_systolic:.0f}"
                        )


                    with range_col2:

                        # Display diastolic range
                        st.metric(
                            "Diastolic Range",
                            f"{minimum_diastolic:.0f} - "
                            f"{maximum_diastolic:.0f}"
                        )


                    # -------------------------------------------------
                    # AM VS PM
                    # -------------------------------------------------

                    st.markdown(
                        "### AM vs PM"
                    )


                    # Keep only readings with AM/PM labels
                    period_df = filtered_df[
                        filtered_df["period"].isin(
                            ["AM", "PM"]
                        )
                    ].copy()


                    if period_df.empty:

                        # Tell the user there is not enough period data
                        st.info(
                            "There are not enough AM/PM labels "
                            "to compare morning and evening readings."
                        )

                    else:

                        # Calculate AM/PM averages
                        period_summary = (
                            period_df
                            .groupby("period")
                            [
                                [
                                    "systolic",
                                    "diastolic",
                                    "pulse"
                                ]
                            ]
                            .mean()
                            .round(1)
                        )


                        # Display the comparison table
                        st.dataframe(
                            period_summary,
                            width="stretch"
                        )


                    # -------------------------------------------------
                    # BLOOD PRESSURE TREND
                    # -------------------------------------------------

                    st.markdown(
                        "### Blood Pressure Trend"
                    )


                    # Create chart data
                    chart_df = filtered_df[
                        [
                            "reading_date",
                            "systolic",
                            "diastolic"
                        ]
                    ].copy()


                    # Calculate daily averages
                    chart_df = (
                        chart_df
                        .groupby(
                            "reading_date"
                        )
                        [
                            [
                                "systolic",
                                "diastolic"
                            ]
                        ]
                        .mean()
                    )


                    # Display the blood pressure trend
                    st.line_chart(
                        chart_df,
                        width="stretch"
                    )


                    # -------------------------------------------------
                    # PULSE TREND
                    # -------------------------------------------------

                    st.markdown(
                        "### Pulse Trend"
                    )


                    # Create pulse chart data
                    pulse_df = filtered_df[
                        [
                            "reading_date",
                            "pulse"
                        ]
                    ].copy()


                    # Remove missing pulse values
                    pulse_df = pulse_df.dropna(
                        subset=["pulse"]
                    )


                    if pulse_df.empty:

                        # Tell the user there is no pulse data
                        st.info(
                            "No pulse data is available for this period."
                        )

                    else:

                        # Calculate daily average pulse
                        pulse_df = (
                            pulse_df
                            .groupby(
                                "reading_date"
                            )[
                                "pulse"
                            ]
                            .mean()
                        )


                        # Display the pulse trend
                        st.line_chart(
                            pulse_df,
                            width="stretch"
                        )


                    # -------------------------------------------------
                    # MOST RECENT READINGS
                    # -------------------------------------------------

                    st.markdown(
                        "### Recent Readings"
                    )


                    # Show the five newest readings in the selected range
                    recent_df = filtered_df.sort_values(
                        [
                            "reading_date"
                        ],
                        ascending=False
                    ).head(5).copy()


                    # Display only useful columns
                    recent_df = recent_df[
                        [
                            "reading_date",
                            "systolic",
                            "diastolic",
                            "pulse",
                            "period"
                        ]
                    ]


                    # Rename columns for display
                    recent_df = recent_df.rename(
                        columns={
                            "reading_date": "Date",
                            "systolic": "Systolic",
                            "diastolic": "Diastolic",
                            "pulse": "Pulse",
                            "period": "Period"
                        }
                    )


                    # Display recent readings
                    st.dataframe(
                        recent_df,
                        width="stretch",
                        hide_index=True
                    )

        except Exception as e:

            # Display any dashboard error
            st.error(
                f"Could not load dashboard data: {e}"
            )