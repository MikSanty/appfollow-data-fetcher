import requests
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import os
import time

# --- CONFIGURATION ---
# Your AppFollow API Token
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGl2MiIsInN1YiI6MjU5MDg4LCJqdGkiOjkzNDE5LCJzY29wZXMiOiJkcncifQ.ixlXWfHr3mQ-fr7uwml-Rs92BsdUMZzm1W31LSeqEXU"

# !!! IMPORTANT: PASTE YOUR DISCORD WEBHOOK URL HERE !!!
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1417777646107889745/SKJcHpwrQfKX3dBo7QsXju3NlCGjBQ7eXl6GZvp5uSm-0zup95EOWl7eiBIWfl1RynYL" 

# --- GOOGLE SHEETS CONFIGURATION ---
GOOGLE_SHEET_NAME = f"Top Charts {datetime.now().strftime('%Y-%m-%d')}"
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# --- APPFOLLOW API CONFIGURATION ---
# List of genres to fetch in sequence
GENRES_TO_FETCH = [
    ("Overall", "0"),
    ("Social Networking", "6005"),
    ("Productivity", "6007"),
    ("Shopping", "6024"),
    ("Photo & Video", "6008")
]
BASE_URL = "https://api.appfollow.io/api/v2/charts/topcharts"
COUNTRY = "us"
DEVICE = "iphone"

# --- HELPER FUNCTIONS ---

def save_json(data, filename):
    """Saves the given data to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
            print(f"-> Successfully saved API response to '{filename}'")
    except Exception as e:
        print(f"-> Error saving JSON to file: {e}")

def update_google_sheet(spreadsheet, worksheet_name, data_rows):
    """Connects to a worksheet and writes the provided data."""
    try:
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            print(f"-> Found existing worksheet: '{worksheet_name}'. Clearing and updating.")
            worksheet.clear()
        except gspread.WorksheetNotFound:
            num_cols = len(data_rows[0]) if data_rows else 10
            print(f"-> Worksheet '{worksheet_name}' not found. Creating it with {num_cols} columns.")
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows="300", cols=num_cols)

        worksheet.update(data_rows)
        print(f"-> Successfully wrote {len(data_rows) - 1} apps to '{worksheet_name}'.")
    except Exception as e:
        print(f"-> An error occurred while updating Google Sheets: {e}")

def share_spreadsheet_and_get_object(client, sheet_name):
    """Opens or creates a spreadsheet, sets its sharing permissions, and returns the spreadsheet object."""
    try:
        print(f"-> Accessing Google Sheet '{sheet_name}'...")
        spreadsheet = client.open(sheet_name)
        spreadsheet.share(None, perm_type='anyone', role='reader')
        print(f"-> Permissions set to 'Anyone with the link can view'.")
        return spreadsheet
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"-> Spreadsheet '{sheet_name}' not found. Creating and sharing it now.")
        spreadsheet = client.create(sheet_name)
        spreadsheet.share(None, perm_type='anyone', role='reader')
        service_account_email = client.auth.service_account_email
        spreadsheet.share(service_account_email, perm_type='user', role='writer')
        print(f"-> Shared with service account: {service_account_email}")
        return spreadsheet
    except Exception as e:
        print(f"-> An error occurred while sharing the Google Sheet: {e}")
        return None

def send_discord_report(summaries, sheet_url):
    """Formats and sends a consolidated report for all genres to Discord."""
    if "YOUR_WEBHOOK_URL_HERE" in DISCORD_WEBHOOK_URL:
        print("⚠️  Discord webhook URL is not set. Skipping notification.")
        return

    embeds = []
    for summary in summaries:
        top_free_str = "\n".join([f"{i+1}. {app.get('title', 'Unknown App')}" for i, app in enumerate(summary.get('free', [])[:5])])
        if not top_free_str: top_free_str = "No data available."
        
        top_paid_str = "\n".join([f"{i+1}. {app.get('title', 'Unknown App')}" for i, app in enumerate(summary.get('paid', [])[:5])])
        if not top_paid_str: top_paid_str = "No data available."
        
        embed = {
            "title": f"🏆 Top Charts: {summary.get('genre_name', 'Unknown')}",
            "color": 5814783,
            "fields": [
                {"name": "Top 5 Free", "value": top_free_str, "inline": True},
                {"name": "Top 5 Paid", "value": top_paid_str, "inline": True}
            ]
        }
        embeds.append(embed)
    
    payload = {
        "content": f"**Full Report for {datetime.now().strftime('%Y-%m-%d')} is Available on Google Sheets:**\n{sheet_url}",
        "embeds": embeds
    }
    
    try:
        print("\n-> Sending consolidated report to Discord...")
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("-> Successfully sent report to Discord.")
    except requests.exceptions.RequestException as e:
        print(f"-> Error sending message to Discord: {e}")


# --- MAIN SCRIPT ---
def fetch_and_process_charts(spreadsheet, genre_name, genre_id):
    """Fetches charts for a specific genre and returns a summary for Discord."""
    current_date = datetime.now().strftime('%Y-%m-%d')
    headers = { "accept": "application/json", "X-AppFollow-API-Token": API_TOKEN }
    params = { 'country': COUNTRY, 'device': DEVICE, 'genre': genre_id, 'date': current_date }
    
    print(f"\nFetching top charts for genre '{genre_name}' ({genre_id}) on {current_date}...")
    
    try:
        response = requests.get(BASE_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            output_filename = f"appfollow_topcharts_{genre_name.replace(' ', '_')}_{current_date}.json"
            save_json(data, output_filename)
            
            all_apps = data.get('result', [])
            free_apps = [app for app in all_apps if app.get('feed_type') == 'free']
            paid_apps = [app for app in all_apps if app.get('feed_type') == 'paid']

            base_header_map = {
                "Rank": "pos", "App ID": "ext_id", "App Name": "title", "Developer": "artist_name",
                "Avg Rating": "rating_avg", "Rating Count": "rating_cnt", "Position Change": "pos_diff",
                "App Store Link": "url", "Price": "price"
            }
            
            for chart_type, app_list in [('Free', free_apps), ('Paid', paid_apps)]:
                if not app_list: continue

                current_header_map = base_header_map.copy()
                if chart_type == 'Free': del current_header_map["Price"]
                
                headers_in_order = list(current_header_map.keys())
                keys_in_order = list(current_header_map.values())
                
                worksheet_name = f"Top {chart_type} - {genre_name} ({COUNTRY.upper()})"
                data_for_sheet = [headers_in_order]

                for app in app_list:
                    row = []
                    for key in keys_in_order:
                        value = app.get(key, 'N/A')
                        if key == 'url' and isinstance(value, str):
                            value = value.replace('apps.apple.com', 'itunes.apple.com')
                        row.append(value)
                    data_for_sheet.append(row)
                
                update_google_sheet(spreadsheet, worksheet_name, data_for_sheet)

            # Return a summary for the final Discord report
            return {"genre_name": genre_name, "free": free_apps, "paid": paid_apps}
            
        else:
            print(f"❌ Error: API returned status code {response.status_code}. Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred during the request: {e}")
        return None

# --- Run the script ---
if __name__ == "__main__":
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet_obj = share_spreadsheet_and_get_object(client, GOOGLE_SHEET_NAME)
        
        if spreadsheet_obj:
            all_summaries = []
            # Loop through all defined genres
            for name, gid in GENRES_TO_FETCH:
                summary = fetch_and_process_charts(spreadsheet_obj, name, gid)
                if summary:
                    all_summaries.append(summary)
                time.sleep(2) # Pause between API calls to be respectful

            # After all genres are processed, send one Discord report
            if all_summaries:
                send_discord_report(all_summaries, spreadsheet_obj.url)
            
            print("\n✅ Script finished successfully.")
        else:
            print("\n❌ Could not access Google Sheet. Halting script.")

    except FileNotFoundError:
        print(f"-> CRITICAL ERROR: The credentials file '{CREDENTIALS_FILE}' was not found.")
    except Exception as e:
        print(f"-> An unexpected error occurred: {e}")