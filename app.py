from flask import Flask
from CalndarApplication import create_app
from tasks.scheduled_email import schedule_events
import os
from tasks.scheduled_email import scheduler


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = create_app()

if __name__ == '__main__':
    scheduler.add_job(schedule_events, 'interval', minutes=1)
    app.run()

