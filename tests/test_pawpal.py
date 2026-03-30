from pawpal_system import Owner, Pet, Scheduler, Task


def test_add_task_to_pet_sets_pet_name():
    pet = Pet("Mochi", "dog", 3)
    task = Task("Morning walk", 20, "daily")

    pet.add_task(task)

    assert len(pet.tasks) == 1
    assert pet.tasks[0].pet_name == "Mochi"


def test_owner_get_all_tasks_collects_from_multiple_pets():
    owner = Owner("Jordan")
    dog = Pet("Mochi", "dog", 3)
    cat = Pet("Luna", "cat", 2)

    dog.add_task(Task("Morning walk", 20, "daily"))
    cat.add_task(Task("Give medicine", 5, "daily"))

    owner.add_pet(dog)
    owner.add_pet(cat)

    all_tasks = owner.get_all_tasks()

    assert len(all_tasks) == 2
    assert {task.description for task in all_tasks} == {"Morning walk", "Give medicine"}


def test_scheduler_organizes_tasks_by_time():
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog", 3)

    pet.add_task(Task("Morning walk", 20, "daily"))
    pet.add_task(Task("Feed breakfast", 10, "daily"))
    pet.add_task(Task("Give medicine", 5, "daily"))

    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    schedule = scheduler.generate_schedule()

    assert [task.description for task in schedule] == [
        "Give medicine",
        "Feed breakfast",
        "Morning walk",
    ]


def test_scheduler_prioritizes_high_priority_tasks_before_low_priority():
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog", 3)

    pet.add_task(Task("Brush coat", 15, "weekly", priority="low"))
    pet.add_task(Task("Give medicine", 5, "daily", priority="high"))
    pet.add_task(Task("Feed breakfast", 10, "daily", priority="medium"))

    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    schedule = scheduler.generate_schedule()

    assert [task.description for task in schedule] == [
        "Give medicine",
        "Feed breakfast",
        "Brush coat",
    ]


def test_generate_schedule_respects_time_limit_and_keeps_best_tasks():
    owner = Owner("Jordan", available_time=30)
    pet = Pet("Mochi", "dog", 3)

    pet.add_task(Task("Long walk", 15, "daily", priority="medium"))
    pet.add_task(Task("Give medicine", 5, "daily", priority="high"))
    pet.add_task(Task("Feed breakfast", 10, "daily", priority="high"))
    pet.add_task(Task("Brush coat", 15, "weekly", priority="low"))

    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    schedule = scheduler.generate_schedule()

    assert [task.description for task in schedule] == [
        "Give medicine",
        "Feed breakfast",
        "Long walk",
    ]
    assert sum(task.time_minutes for task in schedule) <= 30


def test_scheduler_sort_by_time_orders_hhmm_strings():
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog", 3)

    pet.add_task(Task("Evening walk", 20, "daily", time="18:30"))
    pet.add_task(Task("Feed breakfast", 10, "daily", time="08:00"))
    pet.add_task(Task("Give medicine", 5, "daily", time="07:45"))

    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    ordered = scheduler.sort_by_time()

    assert [task.description for task in ordered] == [
        "Give medicine",
        "Feed breakfast",
        "Evening walk",
    ]


def test_scheduler_filters_tasks_by_completion_status():
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog", 3)

    breakfast = Task("Feed breakfast", 10, "daily")
    walk = Task("Morning walk", 20, "daily")
    walk.mark_complete()

    pet.add_task(breakfast)
    pet.add_task(walk)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    pending = scheduler.filter_tasks(completed=False)
    finished = scheduler.filter_tasks(completed=True)

    assert [task.description for task in pending] == ["Feed breakfast"]
    assert [task.description for task in finished] == ["Morning walk"]


def test_scheduler_filters_tasks_by_pet_name():
    owner = Owner("Jordan")
    dog = Pet("Mochi", "dog", 3)
    cat = Pet("Luna", "cat", 2)

    dog.add_task(Task("Morning walk", 20, "daily"))
    cat.add_task(Task("Clean litter", 10, "daily"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner)

    mochi_tasks = scheduler.filter_tasks(pet_name="Mochi")

    assert [task.description for task in mochi_tasks] == ["Morning walk"]
    assert all(task.pet_name == "Mochi" for task in mochi_tasks)


def test_mark_task_complete_updates_status():
    task = Task("Feed breakfast", 10, "daily")

    task.mark_complete()

    assert task.completed is True


def test_marking_daily_task_complete_creates_next_occurrence():
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog", 3)
    task = Task("Feed breakfast", 10, "daily", priority="high", time="08:00")
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    scheduler.mark_task_complete(task)

    assert task.completed is True
    assert len(pet.tasks) == 2
    next_task = pet.tasks[-1]
    assert next_task is not task
    assert next_task.description == "Feed breakfast"
    assert next_task.completed is False
    assert next_task.frequency == "daily"
    assert next_task.time == "08:00"


def test_marking_weekly_task_complete_creates_next_occurrence():
    owner = Owner("Jordan")
    pet = Pet("Luna", "cat", 2)
    task = Task("Brush coat", 15, "weekly", priority="low", time="12:30")
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    scheduler.mark_task_complete(task)

    assert len(pet.tasks) == 2
    assert pet.tasks[-1].frequency == "weekly"
    assert pet.tasks[-1].completed is False


def test_marking_non_recurring_task_complete_does_not_duplicate():
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog", 3)
    task = Task("Vet visit", 30, "once", priority="high", time="15:00")
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    scheduler.mark_task_complete(task)

    assert task.completed is True
    assert len(pet.tasks) == 1


def test_detect_time_conflicts_returns_warning_messages():
    owner = Owner("Jordan")
    dog = Pet("Mochi", "dog", 3)
    cat = Pet("Luna", "cat", 2)

    dog.add_task(Task("Feed breakfast", 10, "daily", time="08:00"))
    cat.add_task(Task("Give medicine", 5, "daily", time="08:00"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner)

    warnings = scheduler.detect_time_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0]
    assert "Feed breakfast" in warnings[0]
    assert "Give medicine" in warnings[0]


def test_detect_time_conflicts_returns_empty_list_when_clear():
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog", 3)

    pet.add_task(Task("Feed breakfast", 10, "daily", time="08:00"))
    pet.add_task(Task("Morning walk", 20, "daily", time="09:00"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    assert scheduler.detect_time_conflicts() == []
