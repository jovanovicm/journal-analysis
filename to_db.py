import json
import sqlite3

conn = sqlite3.connect('journal_db.db')
cursor = conn.cursor()

# Function to create tables if they don't exist
def create_tables():

    # SQL statement to create the DailyLogs table
    create_daily_logs_table = '''
    CREATE TABLE IF NOT EXISTS DailyLogs (
        log_id INTEGER PRIMARY KEY,
        date TEXT NOT NULL,
        rating INTEGER
    );
    '''

    # SQL statement to create the Activities table
    create_activities_table = '''
    CREATE TABLE IF NOT EXISTS Activities (
        activity_id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    );
    '''

    # SQL statement to create the ActivityInstances table
    create_activity_instances_table = '''
    CREATE TABLE IF NOT EXISTS ActivityInstances (
        instance_id INTEGER PRIMARY KEY,
        log_id INTEGER,
        activity_id INTEGER,
        start_time TEXT,
        duration TEXT,
        description TEXT,
        FOREIGN KEY (log_id) REFERENCES DailyLogs(log_id),
        FOREIGN KEY (activity_id) REFERENCES Activities(activity_id)
    );
    '''

    # Execute the SQL statements
    cursor.execute(create_daily_logs_table)
    cursor.execute(create_activities_table)
    cursor.execute(create_activity_instances_table)

    # Commit changes and close the connection
    conn.commit()

# Ensure tables are created before importing data
create_tables()

def import_json_data(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Insert the daily log
    date = data['Date']
    rating = data['Rating']
    cursor.execute('INSERT INTO DailyLogs (date, rating) VALUES (?, ?)', (date, rating))
    log_id = cursor.lastrowid  # Get the ID of the inserted log

    for wake_period in data['WakePeriods']:
        for activity in wake_period['Activities']:
            # Ensure the activity exists in the Activities table
            name = activity['Name']
            cursor.execute('INSERT OR IGNORE INTO Activities (name) VALUES (?)', (name,))
            cursor.execute('SELECT activity_id FROM Activities WHERE name = ?', (name,))
            activity_id = cursor.fetchone()[0]

            # Insert the activity instance
            start_time = activity['StartTime']
            duration = activity['TotalDuration']  # You might want to convert this to minutes
            description = activity['Description']
            cursor.execute('''INSERT INTO ActivityInstances (log_id, activity_id, start_time, duration, description) 
                              VALUES (?, ?, ?, ?, ?)''', (log_id, activity_id, start_time, duration, description))

    conn.commit()

import_json_data('JSON/1-08-2022.json')
conn.close()