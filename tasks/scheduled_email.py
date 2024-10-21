import datetime
import smtplib
import pymysql
from pymysql import cursors
from email.message import EmailMessage
from dbutils.pooled_db import PooledDB
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
db_host = config.get('database', 'host')
db_port_str = config.get('database', 'port')
db_port = int(db_port_str)
db_user = config.get('database', 'user')
db_passwd = config.get('database', 'passwd')

sender_email = config.get('SMTP', 'sender_email')
sender_password = config.get('SMTP', 'sender_password')

scheduler = BackgroundScheduler()
scheduler.start()

# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S',
#     filename='scheduled_tasks.log',
#     filemode='a'
# )
#
# logger = logging.getLogger(__name__)

POOL = PooledDB(
    creator=pymysql,
    maxconnections=10,
    mincached=2,
    maxcached=5,
    blocking=True,
    setsession=[],
    ping=0,

    host=db_host, port=db_port, user=db_user, passwd=db_passwd, charset='utf8', db='calendarapp'
)


def fetch_all(sql, params):
    conn = POOL.connection()
    cursor = conn.cursor(cursor=cursors.DictCursor)
    cursor.execute(sql, params)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def send_email(subject, body, email):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = email

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, [email], msg.as_string())
    server.quit()


def schedule_events():


    sql = "SELECT name, email, time FROM events WHERE date = CURDATE() AND time <= NOW()"
    events = fetch_all("select event_name, event_date, event_time, email from events", None)

    for event in events:
        name = event['event_name']
        date_str = event['event_date']
        time_str = event['event_time']
        email = event['email']

        # combine date and time
        event_datetime = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        print(event_datetime)
        job_id = f'{email}_{event_datetime}'
        if not any(job.id == job_id for job in scheduler.get_jobs()):
            scheduler.add_job(
                id=job_id,
                func=send_email,
                trigger="date",
                run_date=event_datetime,
                args=(f"Reminder: {name}", f"You have an scheduled event named '{name}' today.", email),
            )


if __name__ == "__main__":
    scheduler.add_job(schedule_events, 'interval', minutes=1)

    try:
        #logger.info("Scheduler started. Press Ctrl+C to exit.")
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        #logger.info("Scheduler stopped.")
