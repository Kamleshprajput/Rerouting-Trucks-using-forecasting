def dynamic_reroute(trucks, new_task, distance_matrix, duration_matrix):
    from .scoring import choose_best_path

    best_cost = float("inf")
    best_truck = None
    best_position = -1

    for truck in trucks:
        route = truck.route[:]
        for i in range(len(route) + 1):
            trial = route[:i] + [new_task] + route[i:]
            cost = choose_best_path(trial, distance_matrix, duration_matrix,
                                    perishable=any(t.is_perishable for t in trial))
            if cost < best_cost:
                best_cost = cost
                best_truck = truck
                best_position = i

    if best_truck:
        best_truck.route = best_truck.route[:best_position] + [new_task] + best_truck.route[best_position:]

    return best_truck.id if best_truck else None
