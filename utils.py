import requests
import time
from .data_models import Task,Truck
from fastapi import HTTPException
from typing import List,Tuple
ORS_API_KEY = "api key"
ORS_MATRIX_URL = "ors matrix distance-time"
ORS_URL = "direction for truck"
HEADERS = {
    "Authorization": ORS_API_KEY,
    "Content-Type": "application/json"
}


def get_ors_matrix(tasks):
    locations = [task.location for task in tasks]
    if len(locations) > 50:
        raise ValueError("ORS supports only 50 locations per request.")

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "locations": locations,
        "metrics": ["distance", "duration"],
        "units": "km"
    }

    response = requests.post(ORS_URL, json=body, headers=headers)
    if response.status_code != 200:
        raise Exception(f"ORS Error: {response.status_code} {response.text}")

    data = response.json()
    task_ids = [task.task_id for task in tasks]
    distance_matrix = {
        task_ids[i]: {task_ids[j]: data["distances"][i][j] for j in range(len(task_ids))}
        for i in range(len(task_ids))
    }
    duration_matrix = {
        task_ids[i]: {task_ids[j]: data["durations"][i][j] for j in range(len(task_ids))}
        for i in range(len(task_ids))
    }
    return distance_matrix, duration_matrix


def satisfies_constraints(route, truck, allow_ghost_flexibility=False):
    return True



from .scoring import choose_best_path
from .utils import get_ors_matrix

def get_route_cost_for_truck(truck, distance_matrix=None, duration_matrix=None):
    """
    Computes the cost of the remaining route for a truck.
    If distance/duration matrix not passed, build it safely.
    """

    future_route = truck.route[truck.current_index:]
    if len(future_route) < 2:
        return 0  # Nothing to compute

    # If matrix not passed, build it from the route itself
    if not distance_matrix or not duration_matrix:
        try:
            # Build matrix only for the tasks in future route
            task_list = list({task.task_id: task for task in future_route}.values())  # Remove duplicates
            distance_matrix, duration_matrix = get_ors_matrix(task_list)
        except Exception as e:
            print(f"[ERROR] Failed to compute ORS matrix: {e}")
            return 0

    # Debug print
    print(f"[INFO] Computing cost for Truck {truck.id} with {len(future_route)} tasks")
    print(f"Task IDs: {[t.task_id for t in future_route]}")

    return choose_best_path(
        route=future_route,
        distance_matrix=distance_matrix,
        duration_matrix=duration_matrix,
        perishable=any(task.is_perishable for task in future_route)
    )



def update_truck_indices(trucks,duration_matrix):
    for truck in trucks:
        route = truck.route
        if truck.current_index >= len(route) - 1:
            continue  # Already at end

        from_task = route[truck.current_index]
        to_task = route[truck.current_index + 1]

        # Simple simulation: if ETA < threshold (simulating that the truck moved), increase index
        eta = duration_matrix.get(from_task.task_id, {}).get(to_task.task_id, 10)
        if eta < 15:  # Simulated threshold for testing
            truck.current_index += 1

def get_eta_to_next(truck:Truck , duration_matrix):
    idx = truck.current_index
    route = truck.route
    if idx < len(route) - 1:
        from_id = route[idx].task_id
        to_id = route[idx + 1].task_id
        return duration_matrix.get(from_id, {}).get(to_id)
    return 0
def compute_distance_duration_matrix(locations: List[List[float]]) -> Tuple[List[List[int]], List[List[int]]]:
    body = {
        "locations": locations,
        "metrics": ["distance", "duration"]
    }

    response = requests.post(ORS_MATRIX_URL, json=body, headers=HEADERS)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=response.text)

    matrix = response.json()
    return matrix["distances"], matrix["durations"]
