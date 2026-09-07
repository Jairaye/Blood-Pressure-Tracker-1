# Import the libraries we need
import os
from io import StringIO

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client


# Load the variables from the .env file
load_dotenv()


# Get our Supabase connection information
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET")


# Check that the connection information exists
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL or SUPABASE_KEY is missing from the .env file.")


# Connect to Supabase
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# This is your friend's Supabase user ID
USER_ID = "77d80369-f144-4e30-9c55-59dd881dccaf"


# Historical blood pressure data
raw_data = """Reading Number,Day,Date,Systolic (mmHg),Diastolic (mmHg),Pulse (bpm),Notes
1,Day 1,07/12,170,109,86,AM
2,Day 1,07/12,173,110,83,AM (40% Tier Peak)
3,Day 1,07/12,164,99,88,PM
4,Day 1,07/12,136,85,93,PM
5,Day 1,07/12,160,97,73,PM
6,Day 1,07/12,164,82,82,PM
7,Day 1,07/12,154,95,74,PM (Post-nap baseline)
8,Day 2,07/13,144,99,72,AM
9,Day 2,07/13,137,75,66,PM (Optimal medicated control)
10,Day 3,07/15,157,102,82,AM (Unmedicated rebound)
11,Day 3,07/15,132,73,98,PM (Pre-medication baseline)
12,Day 3,07/15,154,83,90,PM (Pre-medication baseline)
13,Day 3,07/15,164,83,68,PM (Stubborn systolic peak)
14,Day 4,07/16,167,97,63,AM (High-pressure baseline)
15,Day 4,07/16,164,98,89,PM (Evening baseline)
16,Day 5,07/17,139,86,65,AM (Optimal medicated control)
17,Day 5,07/17,145,94,72,PM (Medicated transition baseline)
18,Day 6,07/18,138,82,63,AM (Optimal medicated control)
19,Day 7,07/19,155,89,68,AM (Elevated resting baseline)
20,Day 7,07/19,172,92,86,PM (Severe high-pressure spike)
21,Day 8,07/20,152,98,61,AM (High diastolic baseline)
22,Day 8,07/20,156,78,66,PM (Isolated systolic elevation)
23,Day 8,07/20,149,103,72,PM (Elevated diastolic spike)
24,Day 8,07/20,156,102,70,Pre-bed (High diastolic baseline)
25,Day 10,07/22,124,67,66,AM (Optimal medicated baseline)
26,Day 10,07/22,132,88,60,PM (Controlled medicated baseline)
27,Day 12,07/24,129,80,87,AM (Controlled medicated baseline)
28,Day 12,07/24,141,89,75,PM (Transition baseline)
29,Day 14,07/26,153,93,109,PM (Elevated pulse)
30,Day 14,07/26,168,106,100,PM (High-pressure spike)
31,Day 16,07/28,173,111,101,PM (Severe peak)
32,Day 17,07/29,130,81,94,AM (Optimal medicated baseline)
33,Day 17,07/29,166,108,91,PM (High-pressure trough spike)
34,Day 18,07/30,144,105,78,AM (Elevated diastolic baseline)
35,Day 18,07/30,123,101,73,PM (Isolated diastolic elevation)
36,Day 18,07/30,160,87,81,PM (Systolic elevation spike)
37,Day 19,07/31,155,108,72,AM (Elevated diastolic spike)
38,Day 19,07/31,160,89,65,PM (Systolic elevation spike)
39,Day 20,08/01,139,96,70,PM (Controlled medicated baseline)
40,Day 21,08/02,152,91,80,PM (Elevated systolic baseline)
41,Day 22,08/03,147,100,67,AM (Elevated diastolic baseline)
42,Day 23,08/04,149,101,75,AM (Elevated diastolic baseline)
43,Day 23,08/04,109,73,108,PM (Optimal BP; elevated pulse)
44,Day 24,08/05,154,88,71,AM (Elevated systolic baseline)
45,Day 24,08/05,132,82,66,PM (Controlled medicated baseline)
46,Day 24,08/05,140,78,63,PM (Controlled medicated baseline)
47,Day 25,08/06,142,76,69,AM (Controlled medicated baseline)
48,Day 25,08/06,135,91,70,PM (Controlled medicated baseline)
49,Day 25,08/06,144,81,,VA Clinic Appointment
50,Day 26,08/07,132,77,74,Controlled medicated baseline
51,Day 26,08/07,116,70,71,Optimal medicated baseline
52,Day 26,08/07,134,82,74,Controlled medicated baseline
53,Day 27,08/08,142,77,74,Controlled medicated baseline
54,Day 28,08/09,156,104,92,High-pressure spike
55,Day 28,08/09,153,89,83,Elevated systolic baseline
56,Day 29,08/10,153,87,87,Elevated systolic baseline
57,Day 29,08/10,133,76,71,Controlled medicated baseline
58,Day 30,08/11,146,81,94,Transition baseline
59,Day 31,08/12,167,98,96,High-pressure spike
60,Day 32,08/13,152,92,81,Elevated baseline
61,Day 33,08/14,147,75,93,Elevated systolic baseline
62,Day 34,08/15,166,106,107,High-pressure spike with elevated pulse
63,Day 35,08/16,147,103,89,Elevated diastolic baseline
64,Day 36,08/17,147,92,84,Elevated baseline
65,Day 37,08/18,172,90,86,Systolic elevation spike
66,Day 37,08/18,186,102,90,Severe high-pressure spike
67,Day 38,08/19,157,106,80,Elevated diastolic spike
68,Day 38,08/19,156,86,93,Elevated systolic baseline
69,Day 39,08/20,142,85,73,Controlled medicated baseline
70,Day 39,08/20,156,72,92,Elevated systolic baseline
71,Day 40,08/21,126,73,79,Optimal medicated baseline
72,Day 41,08/22,140,75,72,Controlled medicated baseline
73,Day 41,08/22,141,73,82,Controlled medicated baseline
74,Day 41,08/22,149,113,98,Severe diastolic spike
75,Day 42,08/23,174,106,90,Severe spike (Unmedicated rebound)
76,Day 42,08/23,186,92,78,Severe spike (180+ crisis threshold)
77,Day 42,08/23,174,103,76,Severe spike (Medication absorption)
78,Day 42,08/23,159,88,87,Transitioning baseline
79,Day 43,08/24,148,73,80,Controlled medicated baseline
80,Day 44,08/25,141,88,84,Controlled medicated baseline
81,Day 44,08/25,147,85,74,Controlled medicated baseline
82,Day 45,08/28,132,77,118,Optimal BP; elevated pulse
83,Day 46,08/30,163,80,82,Systolic elevation spike
84,Day 47,08/31,163,138,75,Critical diastolic spike (Likely cuff error)
85,Day 47,08/31,138,84,71,Controlled baseline (Re-test)
86,Day 47,08/31,161,88,61,Systolic elevation spike
87,Day 48,09/02,155,94,80,Elevated transition baseline
"""


# Read the historical data into a pandas DataFrame
df = pd.read_csv(
    StringIO(raw_data)
)


# Convert the date values to actual dates
# The historical readings are from 2026
df["reading_date"] = pd.to_datetime(
    "2026/" + df["Date"],
    format="%Y/%m/%d"
).dt.date


# Convert the systolic values to integers
df["systolic"] = df["Systolic (mmHg)"].astype(int)


# Convert the diastolic values to integers
df["diastolic"] = df["Diastolic (mmHg)"].astype(int)


# Convert pulse values to numbers while allowing the blank value in reading 49
df["pulse"] = pd.to_numeric(
    df["Pulse (bpm)"],
    errors="coerce"
).astype("Int64")


# Create empty period and notes columns
df["period"] = ""
df["notes"] = ""


# Process the original Notes column
for index, row in df.iterrows():

    # Convert the original note to text
    original_note = str(row["Notes"])

    # Handle missing notes
    if original_note == "nan":
        original_note = ""

    # Check whether the entry begins with AM
    if original_note == "AM":
        df.at[index, "period"] = "AM"
        df.at[index, "notes"] = ""

    elif original_note.startswith("AM "):
        df.at[index, "period"] = "AM"
        df.at[index, "notes"] = original_note[3:].strip()

    # Check whether the entry begins with PM
    elif original_note == "PM":
        df.at[index, "period"] = "PM"
        df.at[index, "notes"] = ""

    elif original_note.startswith("PM "):
        df.at[index, "period"] = "PM"
        df.at[index, "notes"] = original_note[3:].strip()

    # Check whether the entry begins with Pre-bed
    elif original_note.startswith("Pre-bed"):
        df.at[index, "period"] = "Pre-bed"

        # Remove the Pre-bed label from the notes
        remaining_note = original_note[len("Pre-bed"):].strip()

        # Remove surrounding parentheses if present
        if remaining_note.startswith("(") and remaining_note.endswith(")"):
            remaining_note = remaining_note[1:-1].strip()

        df.at[index, "notes"] = remaining_note

    # Entries without an AM/PM period
    else:
        df.at[index, "period"] = ""
        df.at[index, "notes"] = original_note


# Build the records in the format expected by Supabase
records = []


# Loop through every historical reading
for _, row in df.iterrows():

    # Create the reading record
    record = {
        "user_id": USER_ID,
        "reading_date": row["reading_date"].isoformat(),
        "reading_time": None,
        "systolic": int(row["systolic"]),
        "diastolic": int(row["diastolic"]),
        "pulse": None if pd.isna(row["pulse"]) else int(row["pulse"]),
        "period": row["period"] if row["period"] else None,
        "notes": row["notes"] if row["notes"] else None
    }

    # Add the record to our list
    records.append(record)


# Show how many readings are ready for import
print(f"Prepared {len(records)} historical readings.")


# Insert the historical readings into Supabase
response = (
    supabase
    .table("readings")
    .insert(records)
    .execute()
)


# Display the result
print(f"Successfully imported {len(response.data)} readings.")


# Confirm completion
print("Historical import complete.")