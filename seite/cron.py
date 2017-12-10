from django_cron import CronJobBase, Schedule
from Workflow.utils import trelloToSQL, publish

# Add to crontab: */5 * * * * cd /home/scholarium/scholarium_production && source venv/bin/activate && python manage.py runcrons
# TODO: Check if log output is created.

class cron_t2sql(CronJobBase):
    RUN_EVERY_MINS = 60
    
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'Trello to SQL Cronjob'
    
    def do(self):
        trelloToSQL()

class cron_publish(CronJobBase):
    RUN_EVERY_MINS = 10

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'Publish article Cronjob'

    def do(self):
        publish()
