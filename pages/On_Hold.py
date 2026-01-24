import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="On Hold",
    page_icon="⏸️",
    layout="wide"
)

# File paths
DATA_DIR = Path(__file__).parent.parent / "data"
ON_HOLD_FILE = DATA_DIR / "on_hold.csv"
TEAM_FILE = DATA_DIR / "team_members.csv"

# Load team members
team_members = pd.read_csv(TEAM_FILE)["name"].tolist()

# Status options
STATUS_OPTIONS = ["To be started", "In progress", "Done"]

# Status colors
def get_status_color(status):
    colors = {
        "To be started": "#cc0000",   # Red
        "In progress": "#b8860b",      # Dark yellow/gold
        "Done": "#228b22"              # Green
    }
    return colors.get(status, "#808080")

def render_status(status):
    color = get_status_color(status)
    return f'<span style="color: {color}; font-weight: bold;">{status}</span>'

# Load existing tasks
if ON_HOLD_FILE.exists():
    on_hold_tasks = pd.read_csv(ON_HOLD_FILE)
    if "id" not in on_hold_tasks.columns:
        on_hold_tasks.insert(0, "id", range(1, len(on_hold_tasks) + 1))
else:
    on_hold_tasks = pd.DataFrame(columns=["id", "team_member", "label", "description", "status"])

# Store in session state
if "on_hold_tasks" not in st.session_state:
    st.session_state.on_hold_tasks = on_hold_tasks.copy()

# Header
st.title("⏸️ On Hold")
st.markdown("Projects that cannot start immediately")
st.markdown("---")

# Get tasks sorted by team member
display_tasks = st.session_state.on_hold_tasks.sort_values("team_member") if not st.session_state.on_hold_tasks.empty else st.session_state.on_hold_tasks

# Display tasks table with colored status
st.subheader("📋 Projects")

# Filter by team member
filter_options = ["All"] + team_members
selected_filter = st.selectbox("Filter by Team Member", options=filter_options, key="task_filter")
if selected_filter != "All":
    display_tasks = display_tasks[display_tasks["team_member"] == selected_filter]

if not display_tasks.empty:
    # Build HTML table
    html = '<table style="width:100%; border-collapse: collapse;">'
    html += '<tr style="background-color: #f0f2f6;">'
    html += '<th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Team Member</th>'
    html += '<th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Label</th>'
    html += '<th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Description</th>'
    html += '<th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Status</th>'
    html += '</tr>'

    for _, row in display_tasks.iterrows():
        html += '<tr>'
        html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{row["team_member"]}</td>'
        html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{row["label"]}</td>'
        html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{row["description"]}</td>'
        html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{render_status(row["status"])}</td>'
        html += '</tr>'

    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)
else:
    st.info("No projects on hold.")

st.markdown("---")

# Add task form
st.subheader("➕ Add Project")
with st.form("add_task_form"):
    col1, col2 = st.columns(2)
    with col1:
        task_member = st.selectbox("Team Member", options=team_members)
        task_label = st.text_input("Label")
    with col2:
        task_status = st.selectbox("Status", options=STATUS_OPTIONS)
        task_desc = st.text_input("Description")

    if st.form_submit_button("➕ Add Project"):
        # Generate new ID
        new_id = st.session_state.on_hold_tasks["id"].max() + 1 if not st.session_state.on_hold_tasks.empty else 1
        new_task = pd.DataFrame({
            "id": [new_id],
            "team_member": [task_member],
            "label": [task_label],
            "description": [task_desc],
            "status": [task_status]
        })
        st.session_state.on_hold_tasks = pd.concat([st.session_state.on_hold_tasks, new_task], ignore_index=True)
        st.experimental_rerun()

st.markdown("---")

# Update status
if not st.session_state.on_hold_tasks.empty:
    st.subheader("✏️ Update Status")
    col1, col2, col3 = st.columns(3)
    with col1:
        update_member = st.selectbox("Team Member", options=team_members, key="update_member")
    filtered_update = st.session_state.on_hold_tasks[st.session_state.on_hold_tasks["team_member"] == update_member]
    if not filtered_update.empty:
        task_options = {f"{row['label']} - {row['description'][:30]}..." if len(str(row['description'])) > 30 else f"{row['label']} - {row['description']}": row['id'] for _, row in filtered_update.iterrows()}
        with col2:
            task_to_update = st.selectbox("Select project", options=list(task_options.keys()), key="update_task")
        with col3:
            new_status = st.selectbox("New status", options=STATUS_OPTIONS, key="new_status")
        if st.button("✏️ Update Status"):
            task_id = task_options[task_to_update]
            st.session_state.on_hold_tasks.loc[st.session_state.on_hold_tasks["id"] == task_id, "status"] = new_status
            st.experimental_rerun()
    else:
        st.info(f"No projects for {update_member}.")

st.markdown("---")

# Delete task
if not st.session_state.on_hold_tasks.empty:
    st.subheader("🗑️ Delete Project")
    col1, col2 = st.columns(2)
    with col1:
        delete_member = st.selectbox("Team Member", options=team_members, key="delete_member")
    filtered_delete = st.session_state.on_hold_tasks[st.session_state.on_hold_tasks["team_member"] == delete_member]
    if not filtered_delete.empty:
        delete_options = {f"{row['label']} - {row['description'][:30]}..." if len(str(row['description'])) > 30 else f"{row['label']} - {row['description']}": row['id'] for _, row in filtered_delete.iterrows()}
        with col2:
            task_display = st.selectbox("Select project to delete", options=list(delete_options.keys()))
        if st.button("🗑️ Delete Project"):
            task_id = delete_options[task_display]
            st.session_state.on_hold_tasks = st.session_state.on_hold_tasks[st.session_state.on_hold_tasks["id"] != task_id]
            st.experimental_rerun()
    else:
        st.info(f"No projects for {delete_member}.")

st.markdown("---")

# Save button
if st.button("💾 Save Changes"):
    st.session_state.on_hold_tasks.to_csv(ON_HOLD_FILE, index=False)
    st.success("On Hold projects saved!")
