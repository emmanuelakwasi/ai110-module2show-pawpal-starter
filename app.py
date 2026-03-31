import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")


def tasks_to_rows(tasks: list[Task]) -> list[dict[str, str | int]]:
    """Convert Task objects into a table-friendly format for Streamlit."""
    return [
        {
            "Time": task.time or "Anytime",
            "Task": task.description,
            "Pet": task.pet_name or "Unassigned",
            "Duration (min)": task.time_minutes,
            "Priority": task.priority.title(),
            "Frequency": task.frequency.title(),
            "Status": "Done" if task.completed else "Pending",
        }
        for task in tasks
    ]


st.title("🐾 PawPal+")

st.markdown(
    """
Plan pet care with less guesswork.
PawPal+ builds a daily plan using **priority-aware scheduling**, **time sorting**, and **conflict warnings**.
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
st.caption("Add tasks with a duration, priority, and time. The scheduler will sort and select the best plan.")

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
    st.success(f"Added task: {task_title}")

if st.session_state.tasks:
    st.write("Current task list")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above to build a schedule.")

st.divider()

st.subheader("Build Schedule")
if st.button("Generate schedule", type="primary"):
    if not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        try:
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

            all_tasks = scheduler.get_tasks()
            sorted_tasks = scheduler.sort_by_time()
            pending_tasks = scheduler.filter_tasks(completed=False)
            pet_tasks = scheduler.filter_tasks(pet_name=demo_pet.name)
            plan = scheduler.generate_schedule()
            unscheduled = scheduler.get_unscheduled_tasks()
            conflict_warnings = scheduler.detect_time_conflicts(sorted_tasks)
        except ValueError as exc:
            st.warning(f"Please fix the task inputs: {exc}")
        else:
            for warning in conflict_warnings:
                st.warning(warning)

            if plan:
                st.success("Schedule generated successfully.")
                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("Tasks scheduled", len(plan))
                with metric_col2:
                    st.metric(
                        "Minutes planned",
                        f"{sum(task.time_minutes for task in plan)}/{int(available_time)}",
                    )

                st.markdown("#### Today's scheduled tasks")
                st.table(tasks_to_rows(plan))
            else:
                st.warning(
                    "No tasks fit the current time budget. Try increasing the available time or shortening a task."
                )

            if unscheduled:
                st.info(
                    "Still pending: "
                    + ", ".join(f"{task.description} ({task.priority})" for task in unscheduled)
                )

            st.markdown("#### All tasks sorted by time")
            st.table(tasks_to_rows(sorted_tasks))

            left_col, right_col = st.columns(2)
            with left_col:
                st.markdown("#### Pending tasks")
                st.table(tasks_to_rows(pending_tasks))

            with right_col:
                st.markdown(f"#### Tasks for {demo_pet.name}")
                st.table(tasks_to_rows(pet_tasks))

            st.caption(
                f"Showing {len(all_tasks)} total task(s), sorted with `sort_by_time()` and filtered with `filter_tasks()`."
            )
