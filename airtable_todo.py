from datetime import date

from airtable import airtable


class Record:
    def __init__(self):
        self.record_id: str = None

    # Return a dict in the format used by Airtable's APIs. This includes swapping in IDs for fields which are links
    # to other objects/tables
    def to_dict(self):
        record = dict()
        for k, v in self.__dict__.items():
            if k == 'record_id':
                continue
            field_name = snake_to_natural_format(k)
            if isinstance(v, date):
                v = v.isoformat()
            record[field_name] = v
        return record


class Task(Record):
    table_name = 'Task'

    def __init__(self):
        super().__init__()
        self.type: TaskType = None
        self.done: bool = None
        self.date: date = None
        self.status: str = None

    def to_dict(self):
        res = super().to_dict()
        res['Type'] = [self.type.record_id]
        del res['Status']
        return res


class TaskType(Record):
    table_name = 'Task Type'

    def __init__(self):
        super().__init__()
        self.name: str = None
        self.category: str = None
        self.strict_date: bool = None


class ScheduleType(Record):
    table_name = 'Schedule Type'

    Weekdays = [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday'
    ]

    def __init__(self):
        super().__init__()
        self.name: str = None
        self.interval: int = None
        self.days: [str] = None


class Schedule(Record):
    table_name = 'Schedule'

    def __init__(self):
        super().__init__()
        self.type: ScheduleType = None
        self.task_type: TaskType = None
        self.start: date = None

    @classmethod
    def from_dict(cls, record: dict, id_to_schedule_types: {str: ScheduleType}, id_to_task_type: {str: TaskType}):
        obj: Schedule = record_to_obj(record, Schedule)

        schedule_type = None
        if len(obj.type) == 1:
            type_record_id = obj.type[0]
            schedule_type = id_to_schedule_types[type_record_id]
        if schedule_type is None:
            return None
        obj.type = schedule_type

        task_type = None
        if len(obj.task_type) == 1:
            task_type_record_id = obj.task_type[0]
            task_type = id_to_task_type.get(task_type_record_id)
        if task_type is None:
            return None
        obj.task_type = task_type

        obj.start = date.fromisoformat(obj.start)
        return obj


def natural_to_snake_format(text: str):
    """
    Converts field names to attribute names, e.g. 'Task Type' -> 'task_type'
    """
    text = text.replace(' ', '_')
    return text.lower()


def snake_to_natural_format(text: str):
    """
    Converts attribute names to field names, e.g. 'task_type' -> 'Task Type'
    """
    text = ' '.join(w.capitalize() for w in text.split('_'))
    return text


def record_to_obj(record: dict, classtype: type):
    obj = classtype()
    obj.record_id = record['id']
    fields = record['fields']
    for attribute in obj.__dict__:
        field_name = snake_to_natural_format(attribute)
        if field_name in fields:
            obj.__setattr__(attribute, fields[field_name])
    return obj


class TodoBase:
    def __init__(self, base_id: str):
        self.id = base_id
        self.name = 'Daily Todo'
        self.schedule_types = {s.record_id: s for s in self.get_schedule_types()}
        self.task_types = {t.record_id: t for t in self.get_task_types()}

    def get_tasks(self):
        response = airtable.fetch_all_records(self.id, Task.table_name)
        return [record_to_obj(r, Task) for r in response['records']]

    def get_schedule_types(self) -> []:
        response = airtable.fetch_all_records(self.id, ScheduleType.table_name)
        return [record_to_obj(r, ScheduleType) for r in response['records']]

    def get_task_types(self):
        response = airtable.fetch_all_records(self.id, TaskType.table_name)
        return [record_to_obj(r, TaskType) for r in response['records']]

    def get_schedules(self) -> []:
        response = airtable.fetch_all_records(self.id, Schedule.table_name)
        schedules = []
        for r in response['records']:
            obj = Schedule.from_dict(r, self.schedule_types, self.task_types)
            schedules.append(obj)
        return schedules

    def generate_tasks(self, date: date):

        def create_task_object(task_type: TaskType, task_date: date = date):
            t = Task()
            t.type = task_type
            t.date = task_date
            return t

        schedules: [Schedule] = self.get_schedules()
        tasks: [Task] = []
        for sched in schedules:
            schedule_type = sched.type
            day_of_week_schedule = schedule_type.days is not None
            interval_schedule = schedule_type.interval is not None
            if day_of_week_schedule:
                day = ScheduleType.Weekdays[date.weekday()]
                if day in schedule_type.days:
                    tasks.append(create_task_object(sched.task_type))
            elif interval_schedule:
                days_elapsed = (date - sched.start).days
                if days_elapsed > 0 and days_elapsed % schedule_type.interval == 0:
                    tasks.append(create_task_object(sched.task_type))
            else:
                print("ERROR: unknown schedule type: %s" % sched.__dict__)
                continue
        return tasks

    def create_tasks(self, tasks: [Task]):
         return airtable.create_records(self.id, Task.table_name, [t.to_dict() for t in tasks])


if __name__ == '__main__':
    from local_definitions import TODO_BASE_ID as BASE_ID

    base = TodoBase(BASE_ID)
    new_tasks = base.generate_tasks(date.today())
    for t in new_tasks:
        print("New task: %s" % t.type.name)
    response = base.create_tasks(new_tasks)
    print(response)
