import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Plan pet care with less guesswork.
PawPal+ now builds a schedule that **prioritizes urgent tasks** and keeps the plan within the owner's available time.
"""
)

st.divider()

st.subheader("Plan your day")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
age = st.number_input("Pet age", min_value=0, max_value=30, value=2)
available_time = st.number_input("Available time today (minutes)", min_value=0, max_value=480, value=30)

st.markdown("### Tasks")
st.caption("Add tasks with their duration and priority. PawPal+ will choose the best mix that fits your day.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    task_time = st.text_input("Time (HH:MM)", value="08:00")

if st.button("Add task"):
    st.session_state.tasks.append(
        {
            "title": task_title,
            "duration_minutes": int(duration),
            "priority": priority,
            "time": task_time,
        }
    )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
if st.button("Generate schedule"):
    demo_owner = Owner(owner_name or "Pet Parent", available_time=int(available_time))
    demo_pet = Pet(pet_name or "Pet", species, int(age))

    for task_data in st.session_state.tasks:
        demo_pet.add_task(
            Task(
                task_data["title"],
                int(task_data["duration_minutes"]),
                "daily",
                priority=task_data["priority"],
                time=task_data.get("time", ""),
            )
        )

    demo_owner.add_pet(demo_pet)
    scheduler = Scheduler(demo_owner)
    plan = scheduler.generate_schedule()

    if plan:
        st.success("Schedule generated.")
        st.code(scheduler.format_schedule())

        unscheduled = scheduler.get_unscheduled_tasks()
        if unscheduled:
            st.info(
                "Still pending: "
                + ", ".join(f"{task.description} ({task.priority})" for task in unscheduled)
            )
    else:
        st.warning("No tasks fit the current time budget. Try increasing the available time or shortening a task.")

    st.caption("PawPal+ uses priority-aware scheduling so the most important pet care tasks happen first.")
