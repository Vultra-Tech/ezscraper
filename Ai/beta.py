import requests
import json
import hashlib
from datetime import datetime
from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Path to the data file
DATA_FILE = "wiki_updates.json"
WIKI_URL = "https://en.wikipedia.org/w/api.php"

# Function to fetch the latest data from Wikipedia's main page
def fetch_data():
    params = {
        "action": "parse",
        "page": "Main_Page",
        "format": "json",
        "prop": "text",
    }

    try:
        response = requests.get(WIKI_URL, params=params)
        data = response.json()

        # Extract the content (HTML text) of the Wikipedia main page
        page_content = data["parse"]["text"]["*"]

        # Create a hash of the page content to track changes
        page_hash = hashlib.md5(page_content.encode('utf-8')).hexdigest()

        # Read the existing data from the file
        try:
            with open(DATA_FILE, "r") as f:
                stored_data = json.load(f)
        except FileNotFoundError:
            stored_data = {"last_hash": "", "updates": []}

        # Check if the hash has changed (i.e., the content has been updated)
        if page_hash != stored_data["last_hash"]:
            # The content has changed, so update the data
            headlines = ["From today's featured article"]  # You can customize which part of the page you want to track

            # Update the data with the latest information
            new_update = {
                "headlines": headlines,
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }

            stored_data["updates"].append(new_update)
            stored_data["last_hash"] = page_hash  # Update the hash

            # Write the updated data back to the file
            with open(DATA_FILE, "w") as f:
                json.dump(stored_data, f, indent=4)

            print(f"Data updated! Saved at {stored_data['last_updated']}")
        else:
            print("No update detected. Skipping write.")

    except requests.exceptions.RequestException as e:
        print(f"\033[1m" + "E: {e}" + "\033[1m")

# Scheduler to run the fetch_data function periodically (every minute)
scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_data, trigger="interval", seconds=1)
scheduler.start()

@app.route("/")
def home():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"updates": [{"headlines": ["No data available yet."], "last_updated": "Unknown"}]}

    # Ensure there are updates to show
    if data["updates"]:
        latest_update = data["updates"][-1]  # Get the most recent update
    else:
        latest_update = {"headlines": [], "last_updated": "No updates available"}

    return render_template("index.html", headlines=latest_update["headlines"], last_updated=latest_update["last_updated"])

@app.route("/api/updates")
def api_updates():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"updates": []}
    return json.dumps(data)

if __name__ == "__main__":
    app.run(debug=True, port=5001)