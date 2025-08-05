from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
import random

# Solver modules
from solver.dynamic_reroute import dynamic_reroute
from solver.batch_manager import BatchManager
from solver.utils import (
    get_route_cost_for_truck,
    get_ors_matrix,
    update_truck_indices,
)
from solver.single_solver import solve_vrp_with_tasks
from solver.data_models import Task, Truck
from solver.task_utils import create_task_from_input

# Constants
ORS_API_KEY = "Yor api key"
ORS_DIRECTIONS_URL = "ors directions for truck"

# FastAPI setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# In-Memory State
# -------------------------------
trucks: List[Truck] = []
tasks: List[Task] = []
ghost_tasks: List[Task] = []
distance_matrix, duration_matrix = {}, {}

# -------------------------------
# Data Models
# -------------------------------
class TaskInput(BaseModel):
    task_id: str
    location: List[float]  # [lon, lat]
    demand: int
    earliest: int
    latest: int
    is_perishable: bool = False
    is_confirmed: bool = True
    type: str  # "pickup" or "delivery"

class ReroutePayload(BaseModel):
    ghost_task_id: str
    type: str  # "pickup" or "delivery"
    truck_id: int

# -------------------------------
# Helper Functions
# -------------------------------
def distance(loc1, loc2):
    lon1, lat1 = loc1
    lon2, lat2 = loc2
    return ((lon1 - lon2) ** 2 + (lat1 - lat2) ** 2) ** 0.5

def load_and_update_matrix():
    global distance_matrix, duration_matrix
    all_tasks = [task for truck in trucks for task in truck.route] + tasks
    unique_tasks = list({t.task_id: t for t in all_tasks}.values())
    distance_matrix, duration_matrix = get_ors_matrix(unique_tasks)
    update_truck_indices(duration_matrix)

def random_location():
    lat = round(random.uniform(12.93, 13.02), 6)
    lon = round(random.uniform(77.58, 77.64), 6)
    return [lon, lat]

def generate_bulk_data():
    global trucks, tasks, ghost_tasks, distance_matrix, duration_matrix
    depot_location = [77.5946, 12.9716]

    tasks.clear()
    for i in range(20):
        tasks.append(Task(
            task_id=f"T{i+1:02}",
            location=random_location(),
            demand=random.randint(1, 3),
            earliest=0,
            latest=500,
            is_perishable=random.choice([True, False]),
            is_confirmed=True,
            type=random.choice(["pickup", "delivery"]),
            priority=random.uniform(0.5, 1.0)
        ))

    ghost_tasks.clear()
    ghost_tasks = [
    Task(task_id="Milk", location=[77.61, 12.975], demand=1, earliest=0, latest=1000, is_perishable=True, is_confirmed=False, type="pickup", priority=0.8),
    Task(task_id="Eggs", location=[77.59, 12.965], demand=1, earliest=0, latest=1000, is_perishable=True, is_confirmed=False, type="delivery", priority=0.9),
    Task(task_id="Bananas", location=[77.62, 12.97], demand=1, earliest=0, latest=1000, is_perishable=True, is_confirmed=False, type="pickup", priority=0.85),
    Task(task_id="Umbrella", location=[77.63, 12.978], demand=1, earliest=0, latest=1000, is_perishable=False, is_confirmed=False, type="pickup", priority=0.7),
    Task(task_id="Laptop Charger", location=[77.58, 12.969], demand=1, earliest=0, latest=1000, is_perishable=False, is_confirmed=False, type="delivery", priority=0.6),
    Task(task_id="Books", location=[77.595, 12.96], demand=1, earliest=0, latest=1000, is_perishable=False, is_confirmed=False, type="pickup", priority=0.75),
    Task(task_id="Shoes", location=[77.61, 12.96], demand=1, earliest=0, latest=1000, is_perishable=False, is_confirmed=False, type="delivery", priority=0.65),
    Task(task_id="Mobile Cover", location=[77.605, 12.965], demand=1, earliest=0, latest=1000, is_perishable=False, is_confirmed=False, type="pickup", priority=0.8),
    Task(task_id="Notebook", location=[77.598, 12.972], demand=1, earliest=0, latest=1000, is_perishable=False, is_confirmed=False, type="delivery", priority=0.7),
]


    trucks.clear()
    for i in range(6):
     assigned = random.sample(tasks, k=4)
     trucks.append(Truck(
        id=i + 1,
        name=f"Truck {i + 1}",  # <-- Add name
        capacity=10,
        route=[Task(
            task_id=f"DEPOT_{i+1}",
            location=depot_location,
            demand=0,
            earliest=0,
            latest=1000,
            is_confirmed=True,
            is_perishable=False,
            type="depot"
        )] + assigned,
        current_index=0
    ))

    all_tasks = [task for truck in trucks for task in truck.route] + tasks
    unique_tasks = list({t.task_id: t for t in all_tasks}.values())
    distance_matrix, duration_matrix = get_ors_matrix(unique_tasks)

# -------------------------------
# Sample Initialization
# -------------------------------
if not trucks:
    generate_bulk_data()

batcher = BatchManager(trucks, distance_matrix, duration_matrix)

# -------------------------------
# API Endpoints
# -------------------------------
@app.get("/dashboard_state")
def get_dashboard():
    return {
        "trucks": [
            {
                "id": truck.id,
                "name":truck.name,
                "route": [task.task_id for task in truck.route],
                "capacity": truck.capacity,
                "current_index": truck.current_index,
                "route_cost": round(get_route_cost_for_truck(truck, distance_matrix, duration_matrix), 2),
            }
            for truck in trucks
        ],
        "all_tasks": [
            {
                "task_id": t.task_id,
                "location": t.location,
                "type": t.type,
                "is_confirmed": t.is_confirmed,
                "is_perishable": t.is_perishable,
            }
            for t in tasks
        ],
    }

@app.post("/batch_add_task")
def batch_add_task(new_task: TaskInput):
    task = create_task_from_input(new_task)
    tasks.append(task)
    batcher.add_task(task)
    return {"message": "Task queued for batch reroute"}

@app.post("/reroute_with_task")
def reroute_with_task(new_task: TaskInput):
    task = create_task_from_input(new_task)
    tasks.append(task)
    load_and_update_matrix()
    rerouted_truck_id = dynamic_reroute(trucks, task, distance_matrix, duration_matrix)
    return {"rerouted_truck_id": rerouted_truck_id}

@app.post("/reroute_with_ghost")
@app.post("/reroute_with_ghost")
@app.post("/reroute_with_ghost")
def reroute_with_ghost(payload: ReroutePayload):
    ghost = next((g for g in ghost_tasks if g.task_id == payload.ghost_task_id), None)
    if not ghost:
        raise HTTPException(status_code=404, detail="Ghost task not found")

    ghost.type = payload.type

    # Step 1: Filter eligible trucks by capacity
    eligible_trucks = []
    for truck in trucks:
        used_capacity = sum(t.demand for t in truck.route)
        if used_capacity + ghost.demand <= truck.capacity:
            dist_to_ghost = distance(truck.route[-1].location, ghost.location)
            eligible_trucks.append((truck, dist_to_ghost))

    if not eligible_trucks:
        raise HTTPException(status_code=400, detail="No truck has enough capacity for the ghost task.")

    # Step 2: Choose nearest truck among eligible
    eligible_trucks.sort(key=lambda x: x[1])  # sort by distance
    best_truck = eligible_trucks[0][0]

    # Step 3: Update route
    best_truck.route.append(ghost)

    # Step 4: Recalculate matrices after modification
    all_tasks = [task for truck in trucks for task in truck.route] + tasks
    unique_tasks = list({t.task_id: t for t in all_tasks}.values())
    global distance_matrix, duration_matrix
    distance_matrix, duration_matrix = get_ors_matrix(unique_tasks)

    # Step 5: Request new geometry from ORS
    coords = [t.location for t in best_truck.route]
    response = requests.post(
        ORS_DIRECTIONS_URL,
        headers={"Authorization": ORS_API_KEY, "Content-Type": "application/json"},
        json={"coordinates": coords},
    )
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=response.text)

    return {
        "assigned_truck": best_truck.id,
        "route": [t.task_id for t in best_truck.route],
        "updated_cost": round(get_route_cost_for_truck(best_truck, distance_matrix, duration_matrix), 2),
        "geometry": response.json()["features"][0]["geometry"]["coordinates"],
    }

@app.get("/forecast_ghost_tasks", response_model=List[Task])
@app.get("/ghost_tasks", response_model=List[Task])
def get_ghost_tasks():
    return ghost_tasks

@app.get("/truck_route_geom/{truck_id}")
def get_truck_route_geom(truck_id: int):
    truck = next((t for t in trucks if t.id == truck_id), None)
    if not truck:
        return {"error": "Truck not found"}

    coords = [t.location for t in truck.route]
    if len(coords) < 2:
        return {"geometry": []}

    response = requests.post(
        ORS_DIRECTIONS_URL,
        headers={"Authorization": ORS_API_KEY, "Content-Type": "application/json"},
        json={"coordinates": coords},
    )
    if response.status_code != 200:
        return {"error": response.text}

    return {"geometry": response.json()["features"][0]["geometry"]["coordinates"]}

@app.get("/truck_cost/{truck_id}")
def get_truck_cost(truck_id: int):
    truck = next((t for t in trucks if t.id == truck_id), None)
    if not truck:
        return {"error": "Truck not found"}

    cost = get_route_cost_for_truck(truck, distance_matrix, duration_matrix)
    return {"truck_id": truck.id, "route_cost": round(cost, 2)}

@app.post("/update_truck_location/{truck_id}")
def update_truck_location(truck_id: int, payload: dict):
    location = payload.get("location")
    truck = next((t for t in trucks if t.id == truck_id), None)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    truck.current_location = location
    return {"message": "Location updated"}

@app.post("/seed_example_data")
def seed_example_data():
    generate_bulk_data()
    return {
        "message": "Seeded 6 trucks, 20 confirmed tasks, 10 ghost tasks.",
        "num_trucks": len(trucks),
        "num_tasks": len(tasks),
        "num_ghosts": len(ghost_tasks),
    }
