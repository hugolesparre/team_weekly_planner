import streamlit as st
import pandas as pd
from pathlib import Path

WEEK_NUM = 1

st.set_page_config(
    page_title=f"Week {WEEK_NUM} Tasks",
    page_icon="📅",
    layout="wide"
)

# File paths
DATA_DIR = Path(__file__).parent.parent / "data"
TASKS_FILE = DATA_DIR / "weekly_tasks.csv"
TEAM_FILE = DATA_DIR / "team_members.csv"

# Load team members
team_members = pd.read_csv(TEAM_FILE)["name"].tolist()

# Status options
STATUS_OPTIONS = ["To be started", "In progress", "Done"]

# Load existing tasks
if TASKS_FILE.exists():
    all_tasks = pd.read_csv(TASKS_FILE)
    if "id" not in all_tasks.columns:
        all_tasks.insert(0, "id", range(1, len(all_tasks) + 1))
else:
    all_tasks = pd.DataFrame(columns=["id", "week", "team_member", "label", "description", "status"])

# Store in session state
if "all_tasks" not in st.session_state:
    st.session_state.all_tasks = all_tasks.copy()

# Header
st.title(f"📅 Week {WEEK_NUM} Tasks")
st.markdown("---")

# Get tasks for this week
week_tasks = st.session_state.all_tasks[st.session_state.all_tasks["week"] == WEEK_NUM].copy()

# Display editable tasks table
st.subheader("📋 Tasks")
st.caption("Edit cells directly • Click ➕ to add rows • Select rows and press Delete to remove")

# Prepare display dataframe
if not week_tasks.empty:
    display_df = week_tasks[["team_member", "label", "description", "status"]].copy()
else:
    display_df = pd.DataFrame(columns=["team_member", "label", "description", "status"])

# Configure columns for the data editor
column_config = {
    "team_member": st.column_config.SelectboxColumn(
        "Team Member",
        options=team_members,
        required=True,
        width="medium"
    ),
    "label": st.column_config.TextColumn(
        "Label",
        required=True,
        width="medium"
    ),
    "description": st.column_config.TextColumn(
        "Description",
        required=True,
        width="large"
    ),
    "status": st.column_config.SelectboxColumn(
        "Status",
        options=STATUS_OPTIONS,
        required=True,
        width="medium"
    )
}

# Editable table
edited_df = st.data_editor(
    display_df,
    column_config=column_config,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="task_editor"
)

st.markdown("---")

# Save button
if st.button("💾 Save Changes", type="primary"):
    # Remove this week's tasks from all_tasks
    other_tasks = st.session_state.all_tasks[st.session_state.all_tasks["week"] != WEEK_NUM].copy()

    # Add week column and generate new IDs for edited tasks
    if not edited_df.empty:
        new_week_tasks = edited_df.copy()
        new_week_tasks["week"] = WEEK_NUM

        # Generate new IDs
        max_id = st.session_state.all_tasks["id"].max() if not st.session_state.all_tasks.empty else 0
        if pd.isna(max_id):
            max_id = 0
        new_week_tasks["id"] = range(int(max_id) + 1, int(max_id) + 1 + len(new_week_tasks))

        # Reorder columns
        new_week_tasks = new_week_tasks[["id", "week", "team_member", "label", "description", "status"]]

        # Combine with other weeks' tasks
        st.session_state.all_tasks = pd.concat([other_tasks, new_week_tasks], ignore_index=True)
    else:
        st.session_state.all_tasks = other_tasks

    # Save to file
    st.session_state.all_tasks.to_csv(TASKS_FILE, index=False)
    st.success("Tasks saved!")
    st.rerun()
