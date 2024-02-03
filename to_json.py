import re
from datetime import datetime, timedelta
import os
import json

def md_to_string(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return content
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {e}"

def process_markdown_folder(md_folder, json_folder):
    # Ensure the JSON folder exists
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)

    # Loop through all files in the Markdown folder
    for filename in os.listdir(md_folder):
        if filename.endswith('.md'):
            md_file_path = os.path.join(md_folder, filename)
            md_content = md_to_string(md_file_path)

            # Process each markdown file
            if md_content and md_content != "File not found.":
                parsed_data = parse_journal_entry_with_final_assumptions(md_content)
                
                # Construct the JSON filename
                json_filename = os.path.splitext(filename)[0] + '.json'
                json_file_path = os.path.join(json_folder, json_filename)

                # Save the JSON data to a file
                with open(json_file_path, 'w', encoding='utf-8') as json_file:
                    json.dump(parsed_data, json_file, ensure_ascii=False, indent=4)

def convert_time_to_24h_format(time_str, last_time, is_pm):
    """ Convert time to a 24-hour format based on the last processed time and PM flag """
    time_obj = datetime.strptime(time_str, '%I:%M')
    
    # Adjust for PM if necessary
    if is_pm or (last_time is not None and time_obj.hour < last_time.hour and time_obj.hour < 12):
        time_obj += timedelta(hours=12)

    # Check if we've crossed to PM or next day
    if last_time is not None:
        if not is_pm and time_obj.hour >= 12:
            is_pm = True  # Crossing noon to PM
        elif is_pm and time_obj.hour < 12:
            time_obj += timedelta(days=1)  # Crossing to the next day

    return time_obj, is_pm


def calculate_duration(start, end):
    """ Calculate duration between two times and return a formatted string """
    if end < start:
        # If end time is earlier than start time, it means the end time is on the next day
        end += timedelta(days=1)

    duration = end - start
    total_minutes = duration.total_seconds() / 60
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    return f"{hours:02d}:{minutes:02d}:00"

def parse_journal_entry_with_final_assumptions(entry):
    """ Parse the journal entry and return JSON-like data structure """
    lines = entry.strip().split('\n')
    data = {"Date": "", "WakePeriods": []}
    current_wake_period = {"WakeTime": "", "SleepTime": "", "Activities": []}
    activity_counts = {}
    is_pm = False  # Initialize the PM flag
    last_time = None

    for line in lines:
        if re.match(r'^\#\s\d{1,2}/\d{1,2}/\d{4}$', line):
            data["Date"] = line.replace('# ', '')
            
        elif re.match(r'^\d{1,2}:\d{2}', line):
            time, activity_part = line.split(' ', 1)
            time_24, is_pm = convert_time_to_24h_format(time, last_time, is_pm)
            last_time = time_24  # Update the last known time

            # Process activities
            if ' - ' in activity_part:
                activity, description = activity_part.split(' - ', 1)
            else:
                activity = activity_part
                description = None

            if activity.lower() in ["wake up", "bed"]:
                if activity.lower() == "wake up":
                    current_wake_period["WakeTime"] = time_24.strftime('%H:%M')
                elif activity.lower() == "bed":
                    current_wake_period["SleepTime"] = time_24.strftime('%H:%M')
                continue

            # Check if the activity contains "wake up"
            if "wake up" in activity.lower():
                current_wake_period["WakeTime"] = time_24.strftime('%H:%M')

            # If WakeTime is still empty, use the first activity's time
            elif not current_wake_period["WakeTime"] and current_wake_period["Activities"]:
                first_activity_time = current_wake_period["Activities"][0]["StartTime"]
                current_wake_period["WakeTime"] = first_activity_time

            if activity not in activity_counts:
                activity_counts[activity] = 0
            activity_counts[activity] += 1

            if activity_counts[activity] > 1:
                activity_name = f"{activity} {activity_counts[activity]}"
            else:
                activity_name = activity

            activity_obj = {
                "Name": activity_name,
                "StartTime": time_24.strftime('%H:%M'),
                "TotalDuration": "",  # Will be calculated later
                "Description": description if description else None
            }
            current_wake_period["Activities"].append(activity_obj)

        elif re.match(r'^\d+\/\d+', line):
            rating, *description = line.split(' ', 1)
            data["Rating"] = int(rating.split('/')[0])
            data["Description"] = description[0].strip() if description else None

    if not current_wake_period["SleepTime"] and current_wake_period["Activities"]:
        last_activity = current_wake_period["Activities"][-1]
        last_activity_time = datetime.strptime(last_activity["StartTime"], '%H:%M')
        current_wake_period["SleepTime"] = last_activity_time.strftime('%H:%M')

    for activity in current_wake_period["Activities"]:
        start_time = datetime.strptime(activity["StartTime"], '%H:%M')
        if activity != current_wake_period["Activities"][-1]:
            next_activity_time = datetime.strptime(current_wake_period["Activities"][current_wake_period["Activities"].index(activity) + 1]["StartTime"], '%H:%M')
        else:
            next_activity_time = datetime.strptime(current_wake_period["SleepTime"], '%H:%M')
        activity["TotalDuration"] = calculate_duration(start_time, next_activity_time)

    if current_wake_period["Activities"]:
        data["WakePeriods"].append(current_wake_period)

    if "Rating" in data and data["Rating"] == 0:
        del data["Rating"]
    if "Description" in data and not data["Description"]:
        del data["Description"]

    return data

md_folder = 'Markdown'
json_folder = 'JSON'
process_markdown_folder(md_folder, json_folder)


