import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


def get_week_dates(year, week_num):
    """Get start and end date for a given week number (week 1 = first Monday of the year)."""
    # Find the first Monday of the year
    jan1 = datetime(year, 1, 1)
    days_until_monday = (7 - jan1.weekday()) % 7
    if days_until_monday == 0 and jan1.weekday() != 0:
        days_until_monday = 7
    first_monday = jan1 + timedelta(days=days_until_monday)
    if jan1.weekday() == 0:  # Jan 1 is already Monday
        first_monday = jan1

    # Calculate week start and end
    start_date = first_monday + timedelta(weeks=week_num - 1)
    end_date = start_date + timedelta(days=4)  # Monday to Friday
    return start_date, end_date


def get_status_color_rgb(status):
    """Return RGB tuple for status color."""
    colors = {
        "To be started": (204, 0, 0),      # Red
        "In progress": (184, 134, 11),     # Dark yellow/gold
        "Done": (34, 139, 34)              # Green
    }
    return colors.get(status, (0, 0, 0))


def generate_weekly_pdf(week_num, team_members, days_passed, days_remaining, progress_pct):
    """Generate PDF report for a given week."""
    DATA_DIR = Path(__file__).parent / "data"
    TASKS_FILE = DATA_DIR / "weekly_tasks.csv"
    SUPPORT_FILE = DATA_DIR / "daily_support.csv"
    ON_HOLD_FILE = DATA_DIR / "on_hold.csv"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 15, f"2026 Weekly Planner - Week {week_num}", ln=True, align="C")
    pdf.ln(5)

    # Team Section
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Team", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, "My team name", ln=True)
    pdf.cell(0, 8, f"Members: {', '.join(team_members)}", ln=True)
    pdf.ln(5)

    # Year Progress Section
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Year Progress", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Days Passed: {days_passed} | Days Remaining: {days_remaining} | Progress: {progress_pct:.1f}%", ln=True)

    # Draw progress bar
    bar_width = 170
    bar_height = 8
    x_start = pdf.get_x()
    y_start = pdf.get_y() + 2
    filled_width = bar_width * (progress_pct / 100)
    pdf.set_fill_color(200, 200, 200)
    pdf.rect(x_start, y_start, bar_width, bar_height, "F")
    pdf.set_fill_color(30, 136, 229)
    pdf.rect(x_start, y_start, filled_width, bar_height, "F")
    pdf.ln(15)

    # Tasks Section
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Week {week_num} Tasks", ln=True)

    if TASKS_FILE.exists():
        tasks_df = pd.read_csv(TASKS_FILE)
        week_tasks = tasks_df[tasks_df["week"] == week_num].sort_values(["team_member", "label"])

        if not week_tasks.empty:
            # Group tasks by team member
            col_widths = [40, 90, 40]
            headers = ["Label", "Description", "Status"]

            for member in sorted(week_tasks["team_member"].unique()):
                member_tasks = week_tasks[week_tasks["team_member"] == member]

                # Team member name as sub-header
                pdf.set_font("Arial", "B", 11)
                pdf.set_fill_color(230, 230, 230)
                pdf.cell(0, 8, member, ln=True, fill=True)

                # Table header
                pdf.set_font("Arial", "B", 9)
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 7, header, 1, 0, "C")
                pdf.ln()

                # Tasks rows
                pdf.set_font("Arial", "", 9)
                for _, row in member_tasks.iterrows():
                    pdf.cell(col_widths[0], 7, str(row["label"])[:25], 1, 0)
                    desc = str(row["description"])[:55] + "..." if len(str(row["description"])) > 55 else str(row["description"])
                    pdf.cell(col_widths[1], 7, desc, 1, 0)
                    # Set status color
                    r, g, b = get_status_color_rgb(row["status"])
                    pdf.set_text_color(r, g, b)
                    pdf.cell(col_widths[2], 7, str(row["status"]), 1, 0)
                    pdf.set_text_color(0, 0, 0)  # Reset to black
                    pdf.ln()

                pdf.ln(3)  # Space between team members
        else:
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 8, "No tasks for this week.", ln=True)
    else:
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 8, "No tasks file found.", ln=True)

    # Start new page for Support Section
    pdf.add_page()

    # Support Section
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Week {week_num} Support Schedule", ln=True)

    if SUPPORT_FILE.exists():
        support_df = pd.read_csv(SUPPORT_FILE)
        support_df["date"] = pd.to_datetime(support_df["date"])

        start_date, end_date = get_week_dates(2026, week_num)
        week_support = support_df[(support_df["date"] >= start_date) & (support_df["date"] <= end_date)]

        if not week_support.empty:
            pdf.set_font("Arial", "B", 10)
            col_widths = [40, 65, 65]
            headers = ["Date", "Primary", "Secondary"]
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 8, header, 1, 0, "C")
            pdf.ln()

            pdf.set_font("Arial", "", 9)
            for _, row in week_support.iterrows():
                pdf.cell(col_widths[0], 7, row["date"].strftime("%a %Y-%m-%d"), 1, 0)
                pdf.cell(col_widths[1], 7, str(row["primary_support"]) if pd.notna(row["primary_support"]) else "", 1, 0)
                pdf.cell(col_widths[2], 7, str(row["secondary_support"]) if pd.notna(row["secondary_support"]) else "", 1, 0)
                pdf.ln()
        else:
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 8, "No support schedule for this week.", ln=True)
    else:
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 8, "No support file found.", ln=True)

    pdf.ln(5)

    # On Hold Section
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Projects On Hold", ln=True)

    if ON_HOLD_FILE.exists():
        on_hold_df = pd.read_csv(ON_HOLD_FILE)

        if not on_hold_df.empty:
            on_hold_df = on_hold_df.sort_values(["team_member", "label"])
            col_widths = [40, 90, 40]
            headers = ["Label", "Description", "Status"]

            for member in sorted(on_hold_df["team_member"].unique()):
                member_tasks = on_hold_df[on_hold_df["team_member"] == member]

                # Team member name as sub-header
                pdf.set_font("Arial", "B", 11)
                pdf.set_fill_color(230, 230, 230)
                pdf.cell(0, 8, member, ln=True, fill=True)

                # Table header
                pdf.set_font("Arial", "B", 9)
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 7, header, 1, 0, "C")
                pdf.ln()

                # Tasks rows
                pdf.set_font("Arial", "", 9)
                for _, row in member_tasks.iterrows():
                    pdf.cell(col_widths[0], 7, str(row["label"])[:25], 1, 0)
                    desc = str(row["description"])[:55] + "..." if len(str(row["description"])) > 55 else str(row["description"])
                    pdf.cell(col_widths[1], 7, desc, 1, 0)
                    # Set status color
                    r, g, b = get_status_color_rgb(row["status"])
                    pdf.set_text_color(r, g, b)
                    pdf.cell(col_widths[2], 7, str(row["status"]), 1, 0)
                    pdf.set_text_color(0, 0, 0)  # Reset to black
                    pdf.ln()

                pdf.ln(3)  # Space between team members
        else:
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 8, "No projects on hold.", ln=True)
    else:
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 8, "No on-hold file found.", ln=True)

    # Return PDF as bytes
    return bytes(pdf.output())


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
        "To be started": "#cc0000",
        "In progress": "#b8860b",
        "Done": "#228b22"
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
                new_task = pd.DataFrame({{
                    "id": [new_id],
                    "week": [WEEK_NUM],
                    "team_member": [new_member],
                    "label": [new_label],
                    "description": [new_desc],
                    "status": [new_status]
                }})
                st.session_state.all_tasks = pd.concat([st.session_state.all_tasks, new_task], ignore_index=True)
                st.session_state.all_tasks.to_csv(TASKS_FILE, index=False)
                st.success("Task added!")
                st.experimental_rerun()
            else:
                st.warning("Please fill in Label and Description")

if not week_tasks.empty:
    with st.expander("✏️ Edit Task", expanded=False):
        # Select task to edit
        task_options = {{f"{{row['team_member']}} - {{row['label']}}: {{row['description'][:30]}}...": row['id']
                       for _, row in week_tasks.iterrows()}}
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

st.markdown("---")

# Generate Weekly Report PDF
st.header("📄 Generate Weekly Report")

if not FPDF_AVAILABLE:
    st.error("PDF generation requires fpdf2. Install it with: pip install fpdf2")
else:
    if existing_weeks:
        col1, col2 = st.columns([3, 1])
        with col1:
            report_week = st.selectbox("Select week for report", options=existing_weeks, format_func=lambda x: f"Week {x}", key="report_week")
        with col2:
            st.write("")
            st.write("")
            if st.button("📄 Generate PDF"):
                pdf_bytes = generate_weekly_pdf(
                    week_num=report_week,
                    team_members=team_members,
                    days_passed=days_passed,
                    days_remaining=days_remaining,
                    progress_pct=progress_percentage
                )
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"weekly_report_week_{report_week}.pdf",
                    mime="application/pdf"
                )
    else:
        st.info("Create a week page first to generate a report.")
