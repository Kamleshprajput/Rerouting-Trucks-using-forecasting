from typing import List
from .data_models import Task, Truck
from .utils import satisfies_constraints
from .scoring import choose_best_path

def insert_ghost_node(truck: Truck, ghost_task: Task) -> List[Task]:
    current_route = truck.route
    best_plan = current_route
    min_cost = float("inf")
    for i in range(1, len(current_route)):
        temp_route = current_route[:i] + [ghost_task] + current_route[i:]
        if not satisfies_constraints(temp_route, truck, allow_ghost_flexibility=True):
            continue
        cost = choose_best_path(temp_route, None, None, ghost_task.is_perishable)
        if cost < min_cost:
            min_cost = cost
            best_plan = temp_route
    return best_plan

def upgrade_ghost_to_confirmed(task: Task):
    task.is_confirmed = True
    task.priority = 1.0
    return task