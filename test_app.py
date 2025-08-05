from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Task(BaseModel):
    task_id: str
    location: List[float]
    type: str
    is_confirmed: bool
    is_perishable: bool

class Truck(BaseModel):
    id: int
    capacity: int
    current_index: int = 0
    route: List[Task]

# ✅ Hardcoded test data
tasks = [
    Task(task_id="T01", location=[77.6, 12.9], type="pickup", is_confirmed=True, is_perishable=False),
    Task(task_id="T02", location=[77.61, 12.91], type="delivery", is_confirmed=True, is_perishable=False),
]

trucks = [
    Truck(id=1, capacity=10, route=tasks)
]

@app.get("/dashboard_state")
def dashboard_state():
    print("Returning dashboard data")
    return {
        "trucks": [
            {
                "id": t.id,
                "route": [task.task_id for task in t.route],
                "current_index": t.current_index,
                "capacity": t.capacity
            }
            for t in trucks
        ],
        "all_tasks": [task.dict() for task in tasks]
    }
