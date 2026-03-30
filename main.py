from pawpal_system import Task, Pet, Owner, Scheduler


def print_task_list(title: str, tasks: list[Task]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    if not tasks:
        print("No matching tasks.")
        return

    for task in tasks:
        status = "Done" if task.completed else "Pending"
        when = task.time or "Anytime"
        print(f"{when} | {task.description} | {task.pet_name} | {task.priority} | {status}")


def main() -> None:
    owner = Owner("Jordan", available_time=30)

    mochi = Pet("Mochi", "dog", 3)
    luna = Pet("Luna", "cat", 2)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Add tasks intentionally out of order and include a shared time slot to show conflict warnings.
    mochi.add_task(Task("Evening walk", 20, "daily", priority="medium", time="18:30"))
    mochi.add_task(Task("Feed breakfast", 10, "daily", priority="high", time="08:00"))
    luna.add_task(Task("Clean litter", 10, "daily", priority="medium", time="09:00"))
    luna.add_task(Task("Give medicine", 5, "daily", priority="high", time="08:00"))
    mochi.add_task(Task("Brush coat", 15, "weekly", priority="low", time="12:30"))

    scheduler = Scheduler(owner)
    mochi.tasks[-1].mark_complete()

    print_task_list("All tasks (added out of order)", scheduler.get_tasks())
    print_task_list("Tasks sorted by time", scheduler.sort_by_time())
    print_task_list("Pending tasks for Mochi", scheduler.filter_tasks(completed=False, pet_name="Mochi"))
    print_task_list("Completed tasks", scheduler.filter_tasks(completed=True))

    warnings = scheduler.detect_time_conflicts()
    if warnings:
        print("\nConflict Warnings")
        print("-----------------")
        for warning in warnings:
            print(warning)

    print("\nDaily Schedule")
    print("--------------")
    print(scheduler.format_schedule())


if __name__ == "__main__":
    main()