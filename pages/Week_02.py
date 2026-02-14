import streamlit as st
import pandas as pd
from pathlib import Path

WEEK_NUM = 2

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

# Status colors
def get_status_color(status):
    colors = {
        "To be started": "#cc0000",
        "In progress": "#b8860b",
        "Done": "#228b22"
    }
    return colors.get(status, "#808080")

def render_status(status):
    color = get_status_color(status)
    return f'<span style="color: {color}; font-weight: bold;">{status}</span>'

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

# Display tasks table
st.subheader("📋 Tasks")

if not week_tasks.empty:
    # Build HTML table
    html = '<table style="width:100%; border-collapse: collapse;">'
    html += '<tr style="background-color: #f0f2f6;">'
    html += '<th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Team Member</th>'
    html += '<th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Label</th>'
    html += '<th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Description</th>'
    html += '<th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Status</th>'
    html += '</tr>'

    for _, row in week_tasks.iterrows():
        html += '<tr>'
        html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{row["team_member"]}</td>'
        html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{row["label"]}</td>'
        html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{row["description"]}</td>'
        html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{render_status(row["status"])}</td>'
        html += '</tr>'

    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)
else:
    st.info("No tasks for this week yet.")

st.markdown("---")

# Use expanders for a cleaner interface
with st.expander("➕ Add New Task", expanded=False):
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_member = st.selectbox("Team Member", options=team_members, key="add_member")
            new_label = st.text_input("Label", key="add_label")
        with col2:
            new_status = st.selectbox("Status", options=STATUS_OPTIONS, key="add_status")
            new_desc = st.text_input("Description", key="add_desc")

        if st.form_submit_button("➕ Add Task"):
            if new_label and new_desc:
                new_id = st.session_state.all_tasks["id"].max() + 1 if not st.session_state.all_tasks.empty else 1
                new_task = pd.DataFrame({
                    "id": [new_id],
                    "week": [WEEK_NUM],
                    "team_member": [new_member],
                    "label": [new_label],
                    "description": [new_desc],
                    "status": [new_status]
                })
                st.session_state.all_tasks = pd.concat([st.session_state.all_tasks, new_task], ignore_index=True)
                st.session_state.all_tasks.to_csv(TASKS_FILE, index=False)
                st.success("Task added!")
                st.experimental_rerun()
            else:
                st.warning("Please fill in Label and Description")

if not week_tasks.empty:
    with st.expander("✏️ Edit Task", expanded=False):
        # Select task to edit
        task_options = {f"{row['team_member']} - {row['label']}: {row['description'][:30]}...": row['id']
                       for _, row in week_tasks.iterrows()}
        selected_task_name = st.selectbox("Select task to edit", options=list(task_options.keys()))
        selected_task_id = task_options[selected_task_name]
        selected_task = week_tasks[week_tasks["id"] == selected_task_id].iloc[0]

        with st.form("edit_task_form"):
            col1, col2 = st.columns(2)
            with col1:
                edit_member = st.selectbox("Team Member", options=team_members,
                                          index=team_members.index(selected_task["team_member"]))
                edit_label = st.text_input("Label", value=selected_task["label"])
            with col2:
                edit_status = st.selectbox("Status", options=STATUS_OPTIONS,
                                          index=STATUS_OPTIONS.index(selected_task["status"]))
                edit_desc = st.text_input("Description", value=selected_task["description"])

            if st.form_submit_button("💾 Save Changes"):
                mask = st.session_state.all_tasks["id"] == selected_task_id
                st.session_state.all_tasks.loc[mask, "team_member"] = edit_member
                st.session_state.all_tasks.loc[mask, "label"] = edit_label
                st.session_state.all_tasks.loc[mask, "description"] = edit_desc
                st.session_state.all_tasks.loc[mask, "status"] = edit_status
                st.session_state.all_tasks.to_csv(TASKS_FILE, index=False)
                st.success("Task updated!")
                st.experimental_rerun()

    with st.expander("🗑️ Delete Task", expanded=False):
        delete_task_name = st.selectbox("Select task to delete", options=list(task_options.keys()), key="delete_select")
        delete_task_id = task_options[delete_task_name]

        if st.button("🗑️ Delete Task"):
            st.session_state.all_tasks = st.session_state.all_tasks[st.session_state.all_tasks["id"] != delete_task_id]
            st.session_state.all_tasks.to_csv(TASKS_FILE, index=False)
            st.success("Task deleted!")
            st.experimental_rerun()
