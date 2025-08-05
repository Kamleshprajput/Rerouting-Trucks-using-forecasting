from solver.data_models import Task

def create_task_from_input(input_data):
    return Task(
        task_id=input_data.task_id,
        location=input_data.location,
        demand=input_data.demand,
        earliest=input_data.earliest,
        latest=input_data.latest,
        is_perishable=input_data.is_perishable,
        is_confirmed=input_data.is_confirmed,
        type=input_data.type,
        priority=1.0 if input_data.is_confirmed else 0.1
    )
