import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="2026 Weekly Planner",
    page_icon="📅",
    layout="wide"
)

# File paths
DATA_DIR = Path(__file__).parent / "data"
PAGES_DIR = Path(__file__).parent / "pages"
TEAM_FILE = DATA_DIR / "team_members.csv"

# Load team members
team_members = pd.read_csv(TEAM_FILE)["name"].tolist()

# Header
st.title("📅 2026 Weekly Planner")
st.markdown("---")

# Team section
st.header("✨ Team")
st.markdown("""
<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;">
    <h2 style="color: #1f77b4; margin: 0;">My team name</h2>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Progress overview section
st.header("📊 Year Progress")

# Calculate days passed and remaining
start_of_year = datetime(2026, 1, 1)
end_of_year = datetime(2026, 12, 31)
today = datetime.now()

if today < start_of_year:
    days_passed = 0
    days_remaining = 365
elif today > end_of_year:
    days_passed = 365
    days_remaining = 0
else:
    days_passed = (today - start_of_year).days
    days_remaining = (end_of_year - today).days

progress_percentage = (days_passed / 365) * 100

# Display progress
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Days Passed", days_passed)

with col2:
    st.metric("Days Remaining", days_remaining)

with col3:
    st.metric("Year Progress", f"{progress_percentage:.1f}%")

# Progress bar
st.progress(progress_percentage / 100)

st.markdown("---")

# --- ADD WEEK PAGE ---
st.header("📋 Manage Week Pages")

# Find existing week pages
existing_weeks = []
for f in PAGES_DIR.glob("Week_*.py"):
    try:
        week_num = int(f.stem.split("_")[1])
        existing_weeks.append(week_num)
    except:
        pass
existing_weeks.sort()

# Add new week page
available_weeks = [w for w in range(1, 53) if w not in existing_weeks]

col1, col2 = st.columns([3, 1])
with col1:
    if available_weeks:
        week_to_create = st.selectbox("Select week to create", options=available_weeks, format_func=lambda x: f"Week {x}")
    else:
        week_to_create = None
        st.success("All 52 week pages have been created!")

with col2:
    st.write("")
    st.write("")
    if week_to_create and st.button("➕ Create Week Page"):
        # Auto-populate tasks from previous week (excluding Done tasks)
        TASKS_FILE = DATA_DIR / "weekly_tasks.csv"
        if TASKS_FILE.exists():
            all_tasks = pd.read_csv(TASKS_FILE)
            if "id" not in all_tasks.columns:
                all_tasks.insert(0, "id", range(1, len(all_tasks) + 1))
            prev_week = week_to_create - 1
            if prev_week > 0:
                # Get tasks from previous week that are not Done
                prev_tasks = all_tasks[(all_tasks["week"] == prev_week) & (all_tasks["status"] != "Done")].copy()
                if not prev_tasks.empty:
                    # Copy tasks to new week with new IDs
                    max_id = all_tasks["id"].max()
                    prev_tasks["week"] = week_to_create
                    prev_tasks["id"] = range(max_id + 1, max_id + 1 + len(prev_tasks))
                    all_tasks = pd.concat([all_tasks, prev_tasks], ignore_index=True)
                    all_tasks.to_csv(TASKS_FILE, index=False)

        # Create the week page file
        week_page_content = f'''import streamlit as st
import pandas as pd
from pathlib import Path

WEEK_NUM = {week_to_create}

st.set_page_config(
    page_title=f"Week {{WEEK_NUM}} Tasks",
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
    colors = {{
        "To be started": "#cc0000",   # Red
        "In progress": "#b8860b",      # Dark yellow/gold
        "Done": "#228b22"              # Green
    }}
    return colors.get(status, "#808080")

def render_status(status):
    color = get_status_color(status)
    return f'<span style="color: {{color}}; font-weight: bold;">{{status}}</span>'

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
st.title(f"📅 Week {{WEEK_NUM}} Tasks")
st.markdown("---")

# Get tasks for this week
week_tasks = st.session_state.all_tasks[st.session_state.all_tasks["week"] == WEEK_NUM].sort_values("team_member")

# Display tasks table with colored status
st.subheader("📋 Tasks")

# Filter by team member
filter_options = ["All"] + team_members
selected_filter = st.selectbox("Filter by Team Member", options=filter_options, key="task_filter")
if selected_filter != "All":
    week_tasks = week_tasks[week_tasks["team_member"] == selected_filter]

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
        html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{{row["team_member"]}}</td>'
        html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{{row["label"]}}</td>'
        html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{{row["description"]}}</td>'
        html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{{render_status(row["status"])}}</td>'
        html += '</tr>'

    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)
else:
    st.info("No tasks for this week yet.")

st.markdown("---")

# Add task form
st.subheader("➕ Add Task")
with st.form("add_task_form"):
    col1, col2 = st.columns(2)
    with col1:
        task_member = st.selectbox("Team Member", options=team_members)
        task_label = st.text_input("Label")
    with col2:
        task_status = st.selectbox("Status", options=STATUS_OPTIONS)
        task_desc = st.text_input("Description")

    if st.form_submit_button("➕ Add Task"):
        # Generate new ID
        new_id = st.session_state.all_tasks["id"].max() + 1 if not st.session_state.all_tasks.empty else 1
        new_task = pd.DataFrame({{
            "id": [new_id],
            "week": [WEEK_NUM],
            "team_member": [task_member],
            "label": [task_label],
            "description": [task_desc],
            "status": [task_status]
        }})
        st.session_state.all_tasks = pd.concat([st.session_state.all_tasks, new_task], ignore_index=True)
        st.experimental_rerun()

st.markdown("---")

# Update status
if not week_tasks.empty:
    st.subheader("✏️ Update Status")
    col1, col2, col3 = st.columns(3)
    with col1:
        update_member = st.selectbox("Team Member", options=team_members, key="update_member")
    filtered_update = week_tasks[week_tasks["team_member"] == update_member]
    if not filtered_update.empty:
        task_options = {{f"{{row['label']}} - {{row['description'][:30]}}..." if len(str(row['description'])) > 30 else f"{{row['label']}} - {{row['description']}}": row['id'] for _, row in filtered_update.iterrows()}}
        with col2:
            task_to_update = st.selectbox("Select task", options=list(task_options.keys()), key="update_task")
        with col3:
            new_status = st.selectbox("New status", options=STATUS_OPTIONS, key="new_status")
        if st.button("✏️ Update Status"):
            task_id = task_options[task_to_update]
            st.session_state.all_tasks.loc[st.session_state.all_tasks["id"] == task_id, "status"] = new_status
            st.experimental_rerun()
    else:
        st.info(f"No tasks for {{update_member}} this week.")

st.markdown("---")

# Delete task
if not week_tasks.empty:
    st.subheader("🗑️ Delete Task")
    col1, col2 = st.columns(2)
    with col1:
        delete_member = st.selectbox("Team Member", options=team_members, key="delete_member")
    filtered_delete = week_tasks[week_tasks["team_member"] == delete_member]
    if not filtered_delete.empty:
        delete_options = {{f"{{row['label']}} - {{row['description'][:30]}}..." if len(str(row['description'])) > 30 else f"{{row['label']}} - {{row['description']}}": row['id'] for _, row in filtered_delete.iterrows()}}
        with col2:
            task_display = st.selectbox("Select task to delete", options=list(delete_options.keys()))
        if st.button("🗑️ Delete Task"):
            task_id = delete_options[task_display]
            st.session_state.all_tasks = st.session_state.all_tasks[st.session_state.all_tasks["id"] != task_id]
            st.experimental_rerun()
    else:
        st.info(f"No tasks for {{delete_member}} this week.")

st.markdown("---")

# Save button
if st.button("💾 Save Changes"):
    st.session_state.all_tasks.to_csv(TASKS_FILE, index=False)
    st.success("Tasks saved!")
'''

        page_file = PAGES_DIR / f"Week_{week_to_create:02d}.py"
        page_file.write_text(week_page_content, encoding="utf-8")
        st.success(f"Week {week_to_create} page created! Refresh to see it in the sidebar.")
        st.experimental_rerun()

st.markdown("---")

# Delete week page
if existing_weeks:
    st.subheader("🗑️ Delete Week Page")
    week_to_delete = st.selectbox("Select week to delete", options=existing_weeks, format_func=lambda x: f"Week {x}")
    if st.button("🗑️ Delete Week Page"):
        page_file = PAGES_DIR / f"Week_{week_to_delete:02d}.py"
        if page_file.exists():
            page_file.unlink()
            st.success(f"Week {week_to_delete} page deleted! Refresh to update sidebar.")
            st.experimental_rerun()
