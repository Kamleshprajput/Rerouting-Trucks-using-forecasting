import time
from typing import List
from .data_models import Task, Truck
from .dynamic_reroute import dynamic_reroute

class BatchManager:
    def __init__(self, trucks: List[Truck], distance_matrix, duration_matrix, batch_size: int = 5, batch_interval: int = 30):
        self.trucks = trucks
        self.distance_matrix = distance_matrix
        self.duration_matrix = duration_matrix
        self.pending_tasks: List[Task] = []
        self.last_flush_time = time.time()
        self.batch_size = batch_size
        self.batch_interval = batch_interval

    def add_task(self, task: Task):
        self.pending_tasks.append(task)
        now = time.time()
        if len(self.pending_tasks) >= self.batch_size or (now - self.last_flush_time) >= self.batch_interval:
            self.flush()

    def flush(self):
        for task in self.pending_tasks:
            dynamic_reroute(
                trucks=self.trucks,
                new_task=task,
                distance_matrix=self.distance_matrix,
                duration_matrix=self.duration_matrix
            )
        self.pending_tasks = []
        self.last_flush_time = time.time()

