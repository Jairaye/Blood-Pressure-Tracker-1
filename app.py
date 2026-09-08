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

        # The access token may simply be stale; try a refresh
        # before treating the session as fully expired
        try:

            refreshed = supabase.auth.refresh_session(
                session.refresh_token
            )

            st.session_state.session = refreshed.session
            session = refreshed.session

        except Exception:

            # Clear an invalid or expired session
            st.session_state.pop(
                "session",
                None
            )

            # Flag this so the login screen can explain why
            st.session_state.session_expired = True

            session = None


# ---------------------------------------------------------
# LOGIN SCREEN
# ---------------------------------------------------------

# Only show this section when the user is not logged in
if session is None:

    # Display the application title
    st.title("Blood Pressure Tracker")

    # Let the user know why they're seeing the login screen again
    if st.session_state.pop("session_expired", False):

        st.info(
            "Your session expired. Please log in again."
        )

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


    # -----------------------------------------------------
    # SHARED VALIDATION HELPERS
    # -----------------------------------------------------

    # Ranges outside of these are flagged as unusual, not blocked
    UNUSUAL_SYSTOLIC_RANGE = (90, 180)
    UNUSUAL_DIASTOLIC_RANGE = (60, 120)
    UNUSUAL_PULSE_RANGE = (40, 120)


    def describe_unusual_values(sys_val, dia_val, pulse_val):
        """Return a list of human-readable warnings for unusual values."""

        warnings = []

        if not (UNUSUAL_SYSTOLIC_RANGE[0] <= sys_val <= UNUSUAL_SYSTOLIC_RANGE[1]):

            warnings.append(
                f"Systolic of {sys_val} is outside the typical "
                f"{UNUSUAL_SYSTOLIC_RANGE[0]}–{UNUSUAL_SYSTOLIC_RANGE[1]} range."
            )

        if not (UNUSUAL_DIASTOLIC_RANGE[0] <= dia_val <= UNUSUAL_DIASTOLIC_RANGE[1]):

            warnings.append(
                f"Diastolic of {dia_val} is outside the typical "
                f"{UNUSUAL_DIASTOLIC_RANGE[0]}–{UNUSUAL_DIASTOLIC_RANGE[1]} range."
            )

        if not (UNUSUAL_PULSE_RANGE[0] <= pulse_val <= UNUSUAL_PULSE_RANGE[1]):

            warnings.append(
                f"Pulse of {pulse_val} is outside the typical "
                f"{UNUSUAL_PULSE_RANGE[0]}–{UNUSUAL_PULSE_RANGE[1]} range."
            )

        return warnings


    # -----------------------------------------------------
    # MEDICATION TAG HELPERS
    #
    # Medication tracking is stored as a small tag prefix on the
    # existing "notes" field, so no database schema change is needed.
    # -----------------------------------------------------

    MEDICATION_TAG = "[Meds <8h]"


    def add_medication_tag(notes_text, medication_flag):
        """Fold the medication flag into notes text for saving."""

        clean_notes = notes_text.strip() if notes_text else ""

        if medication_flag:

            combined = f"{MEDICATION_TAG} {clean_notes}".strip()

        else:

            combined = clean_notes

        return combined if combined else None


    def split_medication_tag(notes_text):
        """Return (medication_flag, notes_without_tag) from stored notes."""

        raw_notes = notes_text or ""

        if raw_notes.startswith(MEDICATION_TAG):

            return True, raw_notes[len(MEDICATION_TAG):].strip()

        return False, raw_notes


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


        # Let the user say the exact time isn't known
        unknown_time = st.checkbox(
            "I don't know the exact time",
            key="add_unknown_time"
        )


        # Only show the time picker when the time is known
        if unknown_time:

            reading_time = None

        else:

            # Use the current time automatically
            reading_time = st.time_input(
                "Reading Time",
                value=datetime.now().time().replace(
                    second=0,
                    microsecond=0
                )
            )


        # -------------------------------------------------
        # MEDICATION (stored as a tag on notes — no schema change)
        # -------------------------------------------------

        st.write("")

        # Simple flag, folded into the notes field on save
        medication_recent = st.checkbox(
            "Took medication within the last 8 hours",
            key="add_medication_recent"
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

            # Hard validation: systolic must be meaningfully above diastolic
            if int(systolic) <= int(diastolic):

                st.error(
                    "Systolic must be higher than diastolic. "
                    "Please double-check these values."
                )

            else:

                # Check for unusual (but not impossible) values
                unusual_warnings = describe_unusual_values(
                    int(systolic),
                    int(diastolic),
                    int(pulse)
                )

                # If there are unusual values and this isn't a confirmed
                # save yet, show the warnings and ask for confirmation
                if unusual_warnings and not st.session_state.get(
                    "add_confirm_unusual",
                    False
                ):

                    for warning_text in unusual_warnings:

                        st.warning(warning_text)

                    st.session_state.add_confirm_unusual = True

                    st.info(
                        "These values look unusual. Click "
                        "\"Save Reading\" again to save anyway, or "
                        "adjust the values above."
                    )

                else:

                    try:

                        # Build the reading record
                        reading = {
                            "user_id": user_id,
                            "reading_date": reading_date.isoformat(),
                            "reading_time": (
                                reading_time.strftime("%H:%M:%S")
                                if reading_time is not None
                                else None
                            ),
                            "systolic": int(systolic),
                            "diastolic": int(diastolic),
                            "pulse": int(pulse),
                            "period": period,
                            "notes": add_medication_tag(
                                notes,
                                medication_recent
                            )
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


                        # Clear the unusual-value confirmation flag
                        st.session_state.pop(
                            "add_confirm_unusual",
                            None
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


                # Let the user say the exact time isn't known
                edit_unknown_time = st.checkbox(
                    "I don't know the exact time",
                    value=editing_reading["reading_time"] is None,
                    key="edit_unknown_time"
                )


                # Only show the time picker when the time is known
                if edit_unknown_time:

                    edit_time = None

                else:

                    # Edit time
                    edit_time = st.time_input(
                        "Reading Time",
                        value=existing_time,
                        key="edit_time"
                    )


                # -------------------------------------------------
                # MEDICATION (tag on notes — no schema change)
                # -------------------------------------------------

                # Pull the medication flag out of the stored notes
                existing_medication_flag, existing_notes_clean = (
                    split_medication_tag(editing_reading["notes"])
                )


                # Edit medication flag
                edit_medication_recent = st.checkbox(
                    "Took medication within the last 8 hours",
                    value=existing_medication_flag,
                    key="edit_medication_recent"
                )


                # Edit notes (shown without the medication tag)
                edit_notes = st.text_area(
                    "Notes",
                    value=existing_notes_clean,
                    key="edit_notes"
                )


                # Confirmation for unusual values (forms can't do a
                # separate confirm step mid-submit, so this is opt-in)
                edit_confirm_unusual = st.checkbox(
                    "I confirm these values are correct even if unusual",
                    key="edit_confirm_unusual"
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

                    # Hard validation: systolic must exceed diastolic
                    if int(edit_systolic) <= int(edit_diastolic):

                        st.error(
                            "Systolic must be higher than diastolic. "
                            "Please double-check these values."
                        )

                    else:

                        # Check for unusual (but not impossible) values
                        edit_unusual_warnings = describe_unusual_values(
                            int(edit_systolic),
                            int(edit_diastolic),
                            int(edit_pulse)
                        )

                        if edit_unusual_warnings and not edit_confirm_unusual:

                            for warning_text in edit_unusual_warnings:

                                st.warning(warning_text)

                            st.info(
                                "Check \"I confirm these values are "
                                "correct even if unusual\" above, then "
                                "click Save Changes again."
                            )

                        else:

                            try:

                                # Create the updated reading
                                updated_reading = {
                                    "reading_date": edit_date.isoformat(),
                                    "reading_time": (
                                        edit_time.strftime("%H:%M:%S")
                                        if edit_time is not None
                                        else None
                                    ),
                                    "systolic": int(edit_systolic),
                                    "diastolic": int(edit_diastolic),
                                    "pulse": int(edit_pulse),
                                    "period": edit_period,
                                    "notes": add_medication_tag(
                                        edit_notes,
                                        edit_medication_recent
                                    )
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

                # -------------------------------------------------
                # FULL DATA BACKUP (unfiltered, always available)
                # -------------------------------------------------

                full_backup_df = pd.DataFrame(readings)

                st.download_button(
                    label="⬇️ Export Everything (Full Backup)",
                    data=full_backup_df.to_csv(index=False),
                    file_name=(
                        f"bp_full_backup_"
                        f"{date.today().isoformat()}.csv"
                    ),
                    mime="text/csv",
                    width="stretch"
                )


                st.divider()


                # -------------------------------------------------
                # PERIOD ICONS (used for compact titles below)
                # -------------------------------------------------

                period_icons = {
                    "AM": "☀️ AM",
                    "PM": "🌇 PM",
                    "Pre-bed": "🌙 Pre-bed"
                }


                # -------------------------------------------------
                # FILTER / SORT / SEARCH CONTROLS
                # -------------------------------------------------

                filter_col, sort_col = st.columns(2)


                with filter_col:

                    # Filter by reading period
                    period_filter = st.selectbox(
                        "Filter by period",
                        [
                            "All",
                            "AM",
                            "PM",
                            "Pre-bed"
                        ],
                        key="history_period_filter"
                    )


                with sort_col:

                    # Choose the sort order
                    sort_order = st.selectbox(
                        "Sort by",
                        [
                            "Newest First",
                            "Oldest First",
                            "Highest Systolic",
                            "Lowest Systolic"
                        ],
                        key="history_sort_order"
                    )


                # Search by a specific date
                search_by_date = st.checkbox(
                    "Search by specific date",
                    key="history_search_toggle"
                )


                search_date = None

                if search_by_date:

                    search_date = st.date_input(
                        "Date",
                        key="history_search_date"
                    )


                # -------------------------------------------------
                # APPLY FILTERS
                # -------------------------------------------------

                filtered_readings = readings


                # Apply the period filter
                if period_filter != "All":

                    filtered_readings = [
                        reading
                        for reading in filtered_readings
                        if reading["period"] == period_filter
                    ]


                # Apply the date search
                if search_date is not None:

                    filtered_readings = [
                        reading
                        for reading in filtered_readings
                        if str(reading["reading_date"]) == search_date.isoformat()
                    ]


                # -------------------------------------------------
                # APPLY SORTING
                # -------------------------------------------------

                if sort_order == "Newest First":

                    filtered_readings = sorted(
                        filtered_readings,
                        key=lambda r: (
                            r["reading_date"],
                            r["reading_time"] or ""
                        ),
                        reverse=True
                    )

                elif sort_order == "Oldest First":

                    filtered_readings = sorted(
                        filtered_readings,
                        key=lambda r: (
                            r["reading_date"],
                            r["reading_time"] or ""
                        )
                    )

                elif sort_order == "Highest Systolic":

                    filtered_readings = sorted(
                        filtered_readings,
                        key=lambda r: r["systolic"],
                        reverse=True
                    )

                elif sort_order == "Lowest Systolic":

                    filtered_readings = sorted(
                        filtered_readings,
                        key=lambda r: r["systolic"]
                    )


                # Show how many readings matched
                st.caption(
                    f"Showing {len(filtered_readings)} of "
                    f"{len(readings)} readings"
                )


                # Export just the currently filtered/sorted readings
                if filtered_readings:

                    filtered_export_df = pd.DataFrame(filtered_readings)

                    st.download_button(
                        label="Download My Readings (CSV)",
                        data=filtered_export_df.to_csv(index=False),
                        file_name=(
                            f"bp_readings_"
                            f"{date.today().isoformat()}.csv"
                        ),
                        mime="text/csv",
                        width="stretch"
                    )


                st.write("")


                # -------------------------------------------------
                # DISPLAY THE READINGS
                # -------------------------------------------------

                if not filtered_readings:

                    # Tell the user nothing matched the filters
                    st.info(
                        "No readings match the selected filters."
                    )

                else:

                    # Display each reading as a compact expandable item
                    for reading in filtered_readings:

                        # Get the reading ID
                        reading_id = reading["id"]


                        # Build the pulse display text
                        pulse_text = (
                            str(reading["pulse"])
                            if reading["pulse"] is not None
                            else "N/A"
                        )


                        # Build the period display text
                        period_text = period_icons.get(
                            reading["period"],
                            reading["period"] or "—"
                        )


                        # Build the combined BP display
                        bp_text = (
                            f'{reading["systolic"]} / '
                            f'{reading["diastolic"]}'
                        )


                        # Pull the medication flag out of stored notes
                        reading_medication_flag, reading_notes_clean = (
                            split_medication_tag(reading["notes"])
                        )


                        # Build the compact, mobile-friendly title
                        reading_title = (
                            f'{reading["reading_date"]}  •  '
                            f'{period_text}  •  '
                            f'{bp_text}  •  '
                            f'{pulse_text} bpm'
                        )

                        if reading_medication_flag:

                            reading_title += "  •  💊"


                        # Create an expandable reading section
                        with st.expander(
                            reading_title
                        ):

                            # Display blood pressure prominently
                            st.markdown(
                                f'### {bp_text}'
                            )


                            # Display time when available
                            if reading["reading_time"]:

                                st.write(
                                    f'**Time:** {reading["reading_time"]}'
                                )


                            # Display pulse
                            st.write(
                                f'**Pulse:** {pulse_text} bpm'
                            )


                            # Display period
                            st.write(
                                f'**Period:** {period_text}'
                            )


                            # Display medication flag
                            if reading_medication_flag:

                                st.write(
                                    "**Medication:** 💊 Taken within "
                                    "the last 8 hours"
                                )


                            # Display notes (medication tag stripped)
                            if reading_notes_clean:

                                st.write(
                                    f'**Notes:** {reading_notes_clean}'
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


                    # -------------------------------------------------
                    # DOCTOR / APPOINTMENT REPORT
                    # -------------------------------------------------

                    st.markdown(
                        "### Doctor / Appointment Report"
                    )


                    # Calculate AM average blood pressure for the report
                    am_readings = filtered_df[
                        filtered_df["period"] == "AM"
                    ]

                    # Calculate PM average blood pressure for the report
                    pm_readings = filtered_df[
                        filtered_df["period"] == "PM"
                    ]


                    # Build the report as plain text
                    report_lines = []

                    report_lines.append("Blood Pressure Summary")

                    report_lines.append(
                        f"{selected_start.strftime('%m/%d/%Y')} - "
                        f"{selected_end.strftime('%m/%d/%Y')}"
                    )

                    report_lines.append("")

                    report_lines.append(
                        f"Average BP: {average_systolic:.0f} / "
                        f"{average_diastolic:.0f}"
                    )

                    if pd.isna(average_pulse):

                        report_lines.append("Average Pulse: N/A")

                    else:

                        report_lines.append(
                            f"Average Pulse: {average_pulse:.0f}"
                        )

                    report_lines.append("")

                    if not am_readings.empty:

                        report_lines.append(
                            f"AM Average: "
                            f"{am_readings['systolic'].mean():.0f} / "
                            f"{am_readings['diastolic'].mean():.0f}"
                        )

                    if not pm_readings.empty:

                        report_lines.append(
                            f"PM Average: "
                            f"{pm_readings['systolic'].mean():.0f} / "
                            f"{pm_readings['diastolic'].mean():.0f}"
                        )

                    report_lines.append("")

                    report_lines.append(
                        f"Highest: {maximum_systolic:.0f} / "
                        f"{maximum_diastolic:.0f}"
                    )

                    report_lines.append(
                        f"Lowest: {minimum_systolic:.0f} / "
                        f"{minimum_diastolic:.0f}"
                    )

                    report_lines.append("")

                    report_lines.append(
                        f"{reading_count} total readings"
                    )

                    report_lines.append("")

                    report_lines.append(
                        "(See trend chart in the app for a visual "
                        "reference of this period.)"
                    )

                    report_text = "\n".join(report_lines)


                    # Show a preview of the report
                    st.text(report_text)


                    # Offer the report as a download
                    st.download_button(
                        label="Download Doctor Report",
                        data=report_text,
                        file_name=(
                            f"bp_doctor_report_"
                            f"{selected_start.strftime('%Y%m%d')}_"
                            f"{selected_end.strftime('%Y%m%d')}.txt"
                        ),
                        mime="text/plain",
                        width="stretch"
                    )

        except Exception as e:

            # Display any dashboard error
            st.error(
                f"Could not load dashboard data: {e}"
            )