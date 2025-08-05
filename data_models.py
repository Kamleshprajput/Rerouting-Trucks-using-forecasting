from typing import List,Optional
from pydantic import BaseModel

class Task(BaseModel):
    task_id: str
    
    location: List[float]
    demand: int
    earliest: int
    latest: int
    is_perishable: bool = False
    is_confirmed: bool = True
    type: str  # "pickup" or "dropoff"
    priority: float = 1.0
   

class Truck(BaseModel):
    id: int
    capacity: int
    route: List[Task] = []
    current_index: int = 0
    current_location: List[float] = []  # [longitude, latitude]
    name:Optional[str]=None