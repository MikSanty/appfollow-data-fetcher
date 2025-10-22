# AppFollow Data Fetcher

Fetch App Store top charts via the AppFollow API, publish results to Google Sheets, and optionally share a digest to Discord.

## Prerequisites
- Python 3.10 or newer
- AppFollow API token with access to the `charts.topcharts` endpoint
- Google Cloud service account JSON key with Drive & Sheets access (saved as `credentials.json` in the project root)
- (Optional) Discord webhook URL for notifications

## Quick Start
1. **Clone the repository**
   ```bash
   git clone https://github.com/MikSanty/appfollow-data-fetcher.git
   cd appfollow-data-fetcher
   ```
2. **Create a virtual environment (recommended)**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```
3. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   ```
4. **Provide credentials**
   1. Visit [Google Cloud Console](https://console.cloud.google.com/) and create a project (or reuse an existing one).
   2. Enable both **Google Sheets API** and **Google Drive API** for that project (APIs & Services ➜ Library ➜ search for each ➜ Enable).
   3. In **APIs & Services ➜ Credentials**, click **Create Credentials ➜ Service Account**. Give it a name, then continue until the account is created (no special roles are required for this script).
   4. Open the new service account, choose the **Keys** tab, and click **Add Key ➜ Create New Key ➜ JSON**. Download the file.
   5. Rename the downloaded file to `credentials.json` and move it into this project folder (alongside `appfollow_data_fetcher.py`).
   6. In Google Sheets, create or open the spreadsheet you want to use, then share it with the service account email address (something like `your-service-account@project.iam.gserviceaccount.com`) with **Editor** access. By default the script looks for a sheet named `Top Charts YYYY-MM-DD` (e.g., `Top Charts 2025-10-22`). Either create that sheet manually each day or set `GOOGLE_SHEET_NAME`/`GOOGLE_SHEET_PREFIX` in your `.env` so the script targets a sheet you have already created and shared. The script can create a sheet on demand, but only when the service account has Drive quota available.
5. **Configure environment variables**
   - Copy `.env.example` to `.env` and fill in the required values:
     ```env
     APPFOLLOW_API_TOKEN=your_appfollow_api_token_here
     DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
     ```
   - `DISCORD_WEBHOOK_URL` may be left blank to skip Discord notifications.
   - Optional overrides: `GOOGLE_SHEET_NAME`, `GOOGLE_SHEET_PREFIX`, `APPFOLLOW_COUNTRY`, `APPFOLLOW_DEVICE`. Setting `GOOGLE_SHEET_NAME` to a permanent sheet you create manually is recommended so the service account does not have to create new spreadsheets.
6. **Run the script**
   ```cmd
   python appfollow_data_fetcher.py
   ```

## What the Script Does
- Fetches the top charts for the predefined genres in `appfollow_data_fetcher.py`.
- Saves the raw API response as `appfollow_topcharts_<Genre>_<date>.json` files (ignored by git).
- Updates or creates worksheets in your Google Sheet for each genre/chart type.
- Shares the sheet publicly (view-only) and optionally posts a summary to Discord.

## Changing Genres
Edit the `GENRES_TO_FETCH` list in `appfollow_data_fetcher.py` to add or remove App Store categories. Each tuple contains the display name and the AppFollow genre ID.

## Troubleshooting
- `Missing APPFOLLOW_API_TOKEN` – Ensure your `.env` file is present and the virtual environment is activated before running Python.
- `credentials.json` not found – Place your Google service account JSON in the project root. If you misplaced it, generate a new key in the Google Cloud Console.
- Discord warns about missing webhook – either supply a webhook URL or leave the field blank to silence the warning.

## Next Steps
- Schedule the script with Windows Task Scheduler or a cron job for regular updates.
- Extend the script to support additional feeds (e.g., grossing charts) or export formats as needed.
