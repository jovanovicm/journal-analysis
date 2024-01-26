import os
import json
import pandas as pd
import matplotlib.pyplot as plt

def read_json_files(json_folder):
    data = []
    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            file_path = os.path.join(json_folder, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = json.load(file)
                date = content.get('Date')
                rating = content.get('Rating', None)
                data.append({'Date': date, 'Rating': rating})
    return data

def extrapolate_missing_ratings(data):
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])
    df.sort_values('Date', inplace=True)
    
    # Fill missing ratings by backfilling, then forward filling
    df['Rating'].fillna(method='bfill', inplace=True)
    df['Rating'].fillna(method='ffill', inplace=True)

    return df

def get_rating_colour(rating):
    """ Return color based on rating """
    if rating <= 3:
        return 'darkred'
    elif rating <= 5:
        return 'red'
    elif rating == 6:
        return 'yellow'
    elif rating <= 8:
        return 'lightgreen'
    else:
        return 'darkgreen'

# Define your JSON folder
json_folder = 'JSON'

# Read and process JSON files
data = read_json_files(json_folder)
df = extrapolate_missing_ratings(data)

# Plotting with color-coded ratings and a connecting line
plt.figure(figsize=(10, 6))

# Plot a line connecting all points
plt.plot(df['Date'], df['Rating'], color='gray', linestyle='-', linewidth=1)

# Overlay color-coded dots
for _, row in df.iterrows():
    plt.plot(row['Date'], row['Rating'], marker='o', color=get_rating_colour(row['Rating']))

plt.title('Ratings Over Time')
plt.xlabel('Date')
plt.ylabel('Rating')
plt.grid(True)
plt.show()