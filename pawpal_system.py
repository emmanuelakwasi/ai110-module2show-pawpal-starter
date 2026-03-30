
from dataclasses import dataclass, field


PRIORITY_VALUES = {"high": 3, "medium": 2, "low": 1}


@dataclass
class Task:
    description: str
    time_minutes: int
    frequency: str
    priority: str = "medium"
    completed: bool = False
    pet_name: str = ""
    time: str = ""

    def __post_init__(self) -> None:
        """Normalize task data for safer scheduling."""
        self.priority = str(self.priority).strip().lower()
        if self.priority not in PRIORITY_VALUES:
            self.priority = "medium"
        if self.time_minutes < 0:
            raise ValueError("time_minutes must be non-negative")

        self.time = str(self.time).strip()
        if self.time:
            try:
                hours, minutes = map(int, self.time.split(":"))
            except ValueError as exc:
                raise ValueError("time must use HH:MM format") from exc

            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError("time must use a valid 24-hour HH:MM value")

    def priority_value(self) -> int:
        """Return a numeric score for sorting and planning."""
        return PRIORITY_VALUES[self.priority]

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def create_next_occurrence(self):
        """Return a fresh copy of this task for the next daily or weekly cycle."""
        if self.frequency not in {"daily", "weekly"}:
            return None

        return Task(
            description=self.description,
            time_minutes=self.time_minutes,
            frequency=self.frequency,
            priority=self.priority,
            completed=False,
            pet_name=self.pet_name,
            time=self.time,
        )

    def get_summary(self) -> str:
        """Return a readable description of the task."""
        status = "Done" if self.completed else "Not done"
        pet_label = f" for {self.pet_name}" if self.pet_name else ""
        time_label = f" at {self.time}" if self.time else ""
        return (
            f"{self.description}{pet_label}{time_label} "
            f"({self.time_minutes} min, {self.frequency}, {self.priority} priority) - {status}"
        )


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task for this pet."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_info(self) -> str:
        """Return a short summary of the pet."""
        return f"{self.name} is a {self.age}-year-old {self.species} with {len(self.tasks)} tasks."


@dataclass
class Owner:
    name: str
    available_time: int = 60
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's household."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Collect tasks from all pets."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self._last_unscheduled_tasks: list[Task] = []

    def get_tasks(self) -> list[Task]:
        """Retrieve all tasks across the owner's pets."""
        return self.owner.get_all_tasks()

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet_name: str | None = None,
        tasks: list[Task] | None = None,
    ) -> list[Task]:
        """Return only the tasks that match the requested pet name and/or completion state."""
        filtered_tasks = self.get_tasks() if tasks is None else list(tasks)

        if completed is not None:
            filtered_tasks = [task for task in filtered_tasks if task.completed is completed]

        if pet_name:
            normalized_pet_name = pet_name.strip().lower()
            filtered_tasks = [
                task for task in filtered_tasks if task.pet_name.strip().lower() == normalized_pet_name
            ]

        return filtered_tasks

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Sort tasks in chronological order by converting each `HH:MM` string into an `(hour, minute)` key."""
        tasks_to_sort = self.get_tasks() if tasks is None else tasks
        return sorted(
            tasks_to_sort,
            key=lambda task: tuple(map(int, task.time.split(":"))) if task.time else (99, 99),
        )

    def detect_time_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Find overlapping task times and return lightweight warning messages instead of raising errors."""
        tasks_to_check = self.get_tasks() if tasks is None else tasks
        timed_tasks = [task for task in tasks_to_check if task.time]
        conflicts_by_time: dict[str, list[Task]] = {}

        for task in timed_tasks:
            conflicts_by_time.setdefault(task.time, []).append(task)

        warnings: list[str] = []
        for time_slot, grouped_tasks in sorted(conflicts_by_time.items()):
            if len(grouped_tasks) > 1:
                details = ", ".join(
                    f"{task.description} ({task.pet_name or 'Unknown pet'})" for task in grouped_tasks
                )
                warnings.append(f"⚠ Warning: {time_slot} has overlapping tasks: {details}")

        return warnings

    def organize_tasks(self, tasks: list[Task] | None = None) -> list[Task]:
        """Sort tasks by completion state, priority, and time needed."""
        tasks_to_sort = self.get_tasks() if tasks is None else tasks
        return sorted(
            tasks_to_sort,
            key=lambda task: (
                task.completed,
                -task.priority_value(),
                task.time_minutes,
                task.description.lower(),
            ),
        )

    def _select_best_task_subset(self, tasks: list[Task], time_limit: int) -> list[Task]:
        """Pick the highest-value set of tasks that fits within the available time budget."""
        if time_limit <= 0 or not tasks:
            return []

        best_by_time: dict[int, tuple[int, int, list[Task]]] = {0: (0, 0, [])}

        for task in tasks:
            snapshot = dict(best_by_time)
            for used_time, (score, count, chosen_tasks) in snapshot.items():
                new_time = used_time + task.time_minutes
                if new_time > time_limit:
                    continue

                candidate = (
                    score + task.priority_value(),
                    count + 1,
                    chosen_tasks + [task],
                )
                current_best = best_by_time.get(new_time)

                if current_best is None or (candidate[0], candidate[1]) > (
                    current_best[0],
                    current_best[1],
                ):
                    best_by_time[new_time] = candidate

        _, (_, _, selected_tasks) = max(
            best_by_time.items(),
            key=lambda item: (item[1][0], item[1][1], item[0]),
        )
        return self.organize_tasks(selected_tasks)

    def generate_schedule(self) -> list[Task]:
        """Create a daily care plan that fits the owner's available time."""
        pending_tasks = [task for task in self.get_tasks() if not task.completed]
        if not pending_tasks:
            self._last_unscheduled_tasks = []
            return []

        schedule = self._select_best_task_subset(
            pending_tasks,
            max(self.owner.available_time, 0),
        )
        scheduled_ids = {id(task) for task in schedule}
        self._last_unscheduled_tasks = self.organize_tasks(
            [task for task in pending_tasks if id(task) not in scheduled_ids]
        )

        if any(task.time for task in schedule):
            return self.sort_by_time(schedule)
        return schedule

    def get_unscheduled_tasks(self) -> list[Task]:
        """Return pending tasks that did not fit into today's plan."""
        return self._last_unscheduled_tasks

    def format_schedule(self) -> str:
        """Format the schedule in a clear terminal-friendly layout."""
        schedule = self.generate_schedule()
        if not schedule:
            return "Today's Schedule\n----------------\nNo tasks fit the current plan."

        planned_minutes = sum(task.time_minutes for task in schedule)
        lines = [
            "Today's Schedule",
            "----------------",
            f"Planned time: {planned_minutes}/{self.owner.available_time} min",
        ]
        for index, task in enumerate(schedule, start=1):
            status = "✓" if task.completed else "○"
            task_time = task.time or "Anytime"
            lines.append(
                f"{index}. {task_time:<7} | {task.description:<18} | {task.time_minutes:>2} min | "
                f"{task.priority:<6} | {status} | Pet: {task.pet_name}"
            )

        conflict_warnings = self.detect_time_conflicts(schedule)
        if conflict_warnings:
            lines.append("")
            lines.append("Warnings:")
            lines.extend(conflict_warnings)

        if self._last_unscheduled_tasks:
            lines.append("")
            lines.append("Still pending:")
            for task in self._last_unscheduled_tasks:
                lines.append(f"- {task.description} ({task.time_minutes} min, {task.priority})")

        return "\n".join(lines)

    def mark_task_complete(self, task: Task) -> None:
        """Complete a task and automatically add the next daily or weekly occurrence when appropriate."""
        if task.completed:
            return

        task.mark_complete()

        next_task = task.create_next_occurrence()
        if not next_task:
            return

        for pet in self.owner.pets:
            if task in pet.tasks:
                pet.add_task(next_task)
                break
