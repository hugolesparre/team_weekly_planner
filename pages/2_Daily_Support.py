import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

st.set_page_config(
    page_title="Daily Support",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Daily Support")
st.markdown("---")

# File paths
DATA_DIR = Path(__file__).parent.parent / "data"
DAILY_FILE = DATA_DIR / "daily_support.csv"
TEAM_FILE = DATA_DIR / "team_members.csv"

# Load team members for dropdown options
team_members = pd.read_csv(TEAM_FILE)["name"].tolist()
team_options = [""] + team_members

# Load existing daily support data
if DAILY_FILE.exists():
    df = pd.read_csv(DAILY_FILE)
else:
    df = pd.DataFrame(columns=["date", "primary_support", "secondary_support"])

# Store in session state
if "daily_df" not in st.session_state:
    st.session_state.daily_df = df.copy()


def get_week_dates(year, week_num):
    """Get Monday to Friday dates for a given week number."""
    # Find the first Monday of the year
    jan1 = date(year, 1, 1)
    # Days until first Monday (0 = Monday)
    days_to_monday = (7 - jan1.weekday()) % 7
    first_monday = jan1 + timedelta(days=days_to_monday)
    if jan1.weekday() == 0:
        first_monday = jan1

    # Get the Monday of the requested week
    week_monday = first_monday + timedelta(weeks=week_num - 1)

    # Return Monday to Friday
    return [week_monday + timedelta(days=i) for i in range(5)]


# --- CALENDAR VIEW (BY WEEK) ---
st.subheader("📆 Week View")

# Week selector
selected_week = st.selectbox("Select Week", options=list(range(1, 53)), index=0, format_func=lambda x: f"Week {x}")

# Get weekdays for selected week
week_dates = get_week_dates(2026, selected_week)

# Display week header with dates
st.markdown("**Mon | Tue | Wed | Thu | Fri**")

# Display the week
cols = st.columns(5)
for i, day_date in enumerate(week_dates):
    with cols[i]:
        date_str = day_date.strftime("%Y-%m-%d")
        day_label = day_date.strftime("%d %b")

        # Check if this day has support assigned
        day_data = st.session_state.daily_df[st.session_state.daily_df["date"] == date_str]

        if not day_data.empty:
            primary = day_data.iloc[0]["primary_support"]
            secondary = day_data.iloc[0]["secondary_support"]
            primary_str = primary if pd.notna(primary) and primary != "" else "-"
            secondary_str = secondary if pd.notna(secondary) and secondary != "" else "-"
            st.markdown(f"**{day_label}**  \n🔵 {primary_str}  \n🟢 {secondary_str}")
        else:
            st.markdown(f"**{day_label}**  \n_empty_")

st.markdown("---")

# --- BULK ADD FORM ---
st.subheader("➕ Add Support (Date Range)")

with st.form("add_range_form"):
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", min_value=date(2026, 1, 1), max_value=date(2026, 12, 31), value=date(2026, 1, 1))
    with col2:
        end_date = st.date_input("End Date", min_value=date(2026, 1, 1), max_value=date(2026, 12, 31), value=date(2026, 1, 1))

    col3, col4 = st.columns(2)
    with col3:
        new_primary = st.selectbox("Primary Support", options=team_options)
    with col4:
        new_secondary = st.selectbox("Secondary Support", options=team_options)

    if st.form_submit_button("➕ Add Days"):
        if start_date <= end_date:
            current_date = start_date
            while current_date <= end_date:
                # Skip weekends
                if current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue

                date_str = current_date.strftime("%Y-%m-%d")
                # Remove existing entry for this date if exists
                st.session_state.daily_df = st.session_state.daily_df[st.session_state.daily_df["date"] != date_str]
                # Add new entry
                new_row = pd.DataFrame({
                    "date": [date_str],
                    "primary_support": [new_primary],
                    "secondary_support": [new_secondary]
                })
                st.session_state.daily_df = pd.concat([st.session_state.daily_df, new_row], ignore_index=True)
                current_date += timedelta(days=1)

            st.session_state.daily_df = st.session_state.daily_df.sort_values("date").reset_index(drop=True)
            st.experimental_rerun()
        else:
            st.error("End date must be after start date")

st.markdown("---")

# --- DELETE SECTION ---
if not st.session_state.daily_df.empty:
    st.subheader("🗑️ Delete Days")

    col1, col2 = st.columns(2)
    with col1:
        delete_start = st.date_input("Delete from", min_value=date(2026, 1, 1), max_value=date(2026, 12, 31), value=date(2026, 1, 1), key="del_start")
    with col2:
        delete_end = st.date_input("Delete to", min_value=date(2026, 1, 1), max_value=date(2026, 12, 31), value=date(2026, 1, 1), key="del_end")

    if st.button("🗑️ Delete Date Range"):
        current_date = delete_start
        while current_date <= delete_end:
            date_str = current_date.strftime("%Y-%m-%d")
            st.session_state.daily_df = st.session_state.daily_df[st.session_state.daily_df["date"] != date_str]
            current_date += timedelta(days=1)
        st.experimental_rerun()

st.markdown("---")

# --- SAVE BUTTON ---
if st.button("💾 Save Changes"):
    st.session_state.daily_df.to_csv(DAILY_FILE, index=False)
    st.success("Daily support schedule saved!")

# --- LEGEND ---
st.markdown("---")
st.caption("🔵 Primary Support | 🟢 Secondary Support")

# --- STATS TABLE ---
st.markdown("---")
st.subheader("📊 Support Stats (Year Total)")

# Build stats for each team member
stats_data = []
for member in team_members:
    primary_count = (st.session_state.daily_df["primary_support"] == member).sum()
    secondary_count = (st.session_state.daily_df["secondary_support"] == member).sum()
    stats_data.append({
        "Team Member": member,
        "Primary Owner (days)": int(primary_count),
        "Secondary Owner (days)": int(secondary_count)
    })

stats_df = pd.DataFrame(stats_data)
st.table(stats_df)
