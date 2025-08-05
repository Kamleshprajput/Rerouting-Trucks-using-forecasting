import random
from solver.data_models import Truck, Task
from solver.utils import get_route_cost_for_truck
from solver.dynamic_reroute import dynamic_reroute
from solver.ghost_forecast import insert_ghost_node

# -------- Matrix Generator --------
def generate_mock_matrices(task_ids):
    matrix = {}
    for i in task_ids:
        matrix[i] = {}
        for j in task_ids:
            if i == j:
                matrix[i][j] = 0
            else:
                matrix[i][j] = random.randint(5, 50)  # Random distance or duration
    return matrix, matrix.copy()

# -------- Generate Tasks --------
task_ids = [f"T{i:02d}" for i in range(15)]
tasks = [
    Task(
        task_id=tid,
        location=[random.uniform(72.0, 73.0), random.uniform(18.0, 19.0)],
        demand=random.randint(1, 3),
        earliest=0,
        latest=1000,
        is_perishable=random.choice([True, False]),
        is_confirmed=True,
        type="pickup"
    )
    for tid in task_ids
]

# -------- Generate Trucks --------
trucks = []
for t_id in range(8):
    assigned_tasks = random.sample(tasks, random.randint(2, 5))
    trucks.append(Truck(id=t_id, capacity=10, route=assigned_tasks))

# -------- Distance & Duration --------
distance_matrix, duration_matrix = generate_mock_matrices(task_ids + ["T99", "T100"])

# -------- Initial Cost Summary --------
print("🔍 Initial Truck Routes and Costs")
total_cost = 0
for truck in trucks:
    cost = get_route_cost_for_truck(truck, distance_matrix, duration_matrix)
    total_cost += cost
    route = [t.task_id for t in truck.route]
    print(f"Truck {truck.id} Route: {route} | Cost: {round(cost, 2)}")
print(f"\n💰 Total Initial Cost: {round(total_cost, 2)}")

# -------- Ghost Task Test --------
ghost_task = Task(
    task_id="T99",
    location=[72.55, 18.6],
    demand=1,
    earliest=0,
    latest=1000,
    is_perishable=False,
    is_confirmed=False,
    type="pickup",
    priority=0.1
)
print(f"\n👻 Inserting Ghost Task {ghost_task.task_id} into Truck 0")
before_cost = get_route_cost_for_truck(trucks[0], distance_matrix, duration_matrix)
trucks[0].route = insert_ghost_node(trucks[0], ghost_task)
after_cost = get_route_cost_for_truck(trucks[0], distance_matrix, duration_matrix)
print(f"Truck 0 Route After Ghost: {[t.task_id for t in trucks[0].route]}")
print(f"Cost Before: {round(before_cost, 2)} → After: {round(after_cost, 2)}")

# -------- Dynamic Task Test --------
dynamic_task = Task(
    task_id="T100",
    location=[72.58, 18.62],
    demand=1,
    earliest=0,
    latest=1000,
    is_perishable=True,
    is_confirmed=True,
    type="pickup",
    priority=1.0
)
print(f"\n🔁 Dynamically Adding Confirmed Task {dynamic_task.task_id}")
rerouted_id = dynamic_reroute(trucks, dynamic_task, distance_matrix, duration_matrix)
updated = next(t for t in trucks if t.id == rerouted_id)
print(f"Task added to Truck {rerouted_id} | New Route: {[t.task_id for t in updated.route]}")
new_cost = get_route_cost_for_truck(updated, distance_matrix, duration_matrix)
print(f"New Route Cost for Truck {rerouted_id}: {round(new_cost, 2)}")

# -------- Final Total Cost --------
total_final = sum(get_route_cost_for_truck(t, distance_matrix, duration_matrix) for t in trucks)
print(f"\n✅ Total Cost After Ghost + Dynamic Tasks: {round(total_final, 2)}")
