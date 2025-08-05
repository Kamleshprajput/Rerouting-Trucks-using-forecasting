from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from solver.utils import compute_distance_duration_matrix

def solve_vrp_with_tasks(truck, task_list):
    coords = [truck.start_location] + [t.location for t in task_list]

    distance_matrix, duration_matrix = compute_distance_duration_matrix(coords)

    manager = pywrapcp.RoutingIndexManager(len(coords), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return int(distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)])
    routing.SetArcCostEvaluatorOfAllVehicles(distance_callback)

    # Add time windows if tasks have earliest/latest
    time = 'Time'
    routing.AddDimension(
        evaluator=distance_callback,
        slack_max=300,
        capacity=100000,
        fix_start_cumul_to_zero=True,
        name=time,
    )
    time_dimension = routing.GetDimensionOrDie(time)

    for idx, task in enumerate(task_list):
        node_index = manager.NodeToIndex(idx + 1)
        if hasattr(task, 'earliest') and hasattr(task, 'latest'):
            time_dimension.CumulVar(node_index).SetRange(task.earliest, task.latest)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_params)

    if not solution:
        raise Exception("No solution found")

    route = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if node != 0:
            route.append(task_list[node - 1])
        index = solution.Value(routing.NextVar(index))

    return route
