from flask import Blueprint, render_template, request, redirect, session, jsonify
from utils import db
import pandas as pd
from datetime import datetime

ev = Blueprint("events", __name__)


@ev.route('/calendar', methods=['GET'])
def get_events():
    date = request.args.get('date')
    user_info = session.get("user_info")
    email = user_info['email']
    events_list = db.fetch_all("select * from events where email=%s and event_date=%s", [email, date])
    return render_template("calendar.html", events_list=events_list)


@ev.route('/api/events', methods=['GET'])
def get_event():
    user_info = session.get("user_info")
    email = user_info['email']
    date = request.args.get('date')

    events = db.fetch_all("select * from events where email=%s and event_date=%s", [email, date])

    def sort_key(event):
        event_time_str = event['event_time']
        event_time_obj = datetime.strptime(event_time_str, '%H:%M')
        return event_time_obj

    sorted_events = sorted(events, key=sort_key)

    json_events = []
    for event in sorted_events:
        json_events.append({
            'date': event['event_date'],
            'name': event['event_name'],
            'time': event['event_time']
        })

    return jsonify(json_events), 200


@ev.route('/api/events/dates', methods=['GET'])
def get_event_dates():
    user_info = session.get("user_info")
    email = user_info['email']
    events = db.fetch_all("select * from events where email=%s ", [email])

    json_event_dates = []
    for event in events:
        json_event_dates.append({
            'date': event['event_date'],
        })

    return jsonify(json_event_dates), 200


@ev.route('/api/events/create', methods=['POST'])
def event_create():
    user_info = session.get("user_info")
    email = user_info['email']
    data = request.get_json()
    event_name = data.get('eventName')
    event_time = data.get('eventTime')
    event_date = data.get('eventDate')

    print(event_name)
    print(event_time)
    print(event_date)

    params = [email, event_name, event_date, event_time]
    db.insert("insert into events(email, event_name, event_date, event_time) values (%s,%s,%s,%s)", params)

    return jsonify({'success': True, 'message': 'Event added successfully.'})


@ev.route('/api/events/upload', methods=['POST'])
def file_event_create():
    user_info = session.get("user_info")
    email = user_info['email']

    file = request.files['file']
    df = pd.read_csv(file, skiprows=1, names=['event_name', 'event_date', 'event_time'], parse_dates=['event_date'])
    print(df)
    df['event_date'] = pd.to_datetime(df['event_date'])
    df['event_date'] = df['event_date'].dt.date

    for _, row in df.iterrows():
        date = row['event_date']
        time = convert_time_format(row['event_time'])

        params = [email, row['event_name'], date, time]
        db.insert("insert into events(email, event_name, event_date, event_time) values (%s,%s,%s,%s)", params)

    return jsonify({"message": "File uploaded successfully!"}), 200


def convert_time_format(time_str):
    time_obj = datetime.strptime(time_str, '%H:%M:%S')
    return time_obj.strftime('%H:%M')
