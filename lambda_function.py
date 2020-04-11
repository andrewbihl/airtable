import airtable_tasks


def lambda_handler(event, context):
    return airtable_tasks.create_tasks_for_today()
