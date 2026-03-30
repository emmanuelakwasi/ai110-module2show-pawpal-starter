
from dataclasses import dataclass, field


@dataclass
class Owner:
    name: str
    available_time: int
    preferences: list[str] = field(default_factory=list)

    def add_preference(self, preference: str) -> None:
        """Add a new owner preference."""
        pass

    def update_available_time(self, minutes: int) -> None:
        """Update how much time the owner has available."""
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int
    needs: list[str] = field(default_factory=list)

    def add_need(self, need: str) -> None:
        """Add a care need for the pet."""
        pass

    def get_info(self) -> str:
        """Return a short summary of the pet."""
        pass


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str
    category: str

    def is_high_priority(self) -> bool:
        """Check whether the task is high priority."""
        pass

    def get_task_details(self) -> str:
        """Return a readable description of the task."""
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to the scheduler."""
        pass

    def sort_by_priority(self) -> list[Task]:
        """Sort tasks by priority level."""
        pass

    def generate_schedule(self) -> list[Task]:
        """Create a daily care plan based on time and priority."""
        pass

    def explain_plan(self) -> str:
        """Explain why tasks were selected for the plan."""
        pass
