def choose_best_path(route, distance_matrix, duration_matrix, perishable):
    total_cost = 0

    print(f"[DEBUG] Route length: {len(route)}")

    for i in range(len(route) - 1):
        from_id = route[i].task_id
        to_id = route[i + 1].task_id

        dist = distance_matrix.get(from_id, {}).get(to_id, 0)
        time = duration_matrix.get(from_id, {}).get(to_id, 0)

        if dist == 0 and time == 0:
            print(f"[WARN] No data for {from_id} ➝ {to_id}")

        if not route[i + 1].is_confirmed:
            weight = 0.2
        elif perishable:
            weight = 1.5
        else:
            weight = 1.0

        step_cost = weight * (dist + 0.5 * time)
        print(f"[DEBUG] {from_id} ➝ {to_id}: dist={dist}, time={time}, weight={weight}, cost={step_cost}")
        total_cost += step_cost

    print(f"[DEBUG] Total Cost: {total_cost}")
    return total_cost

