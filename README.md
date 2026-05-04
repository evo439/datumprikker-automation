# Datumprikker Automator

This script automatically fills in a [Datumprikker](https://datumprikker.nl/) poll based on your Google Calendar availability. It uses Selenium to navigate the web page and the Google Calendar API to check for overlapping events.

## Prerequisites

- Google Chrome installed on your machine.
- Python 3.x installed.

## Setup

1. **Clone this repository** (or download the files).
2. **Configure your details** in `script.py`:
   - Open `script.py`.
   - Update `DATUMPRIKKER_URL` with your unique Datumprikker link.
   - Update `NAAM` and `EMAIL` with your personal information.
   - Modify `EXCLUDED_CALENDARS` if you want the script to check specific calendars only (e.g., ignore holidays).
3. **Google Calendar API Credentials**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project and enable the **Google Calendar API**.
   - Create OAuth 2.0 Client ID credentials (choose Desktop App).
   - Download the JSON file, rename it to `credentials.json`, and place it in the same folder as `script.py`.

## Running the Script

1. Open your terminal or command prompt in the directory containing the files.
2. Run the script:
   ```bash
   python script.py
   ```
3. The script will automatically check and install the required dependencies (using `update_dependencies.py`).
4. **First Run Authentication**: The first time you run the script, a browser window will open asking you to log in to your Google Account and grant read access to your calendars. This creates a `token.json` file so you don't have to log in every time.
5. The script will then launch an automated Chrome browser, navigate to Datumprikker, compare the dates against your Google Calendar, and fill out your availability (Yes/No).
6. It will pause on the final screen so you can review the selections. Press **Enter** in the terminal to close the browser and finish.

## How it works

- **`update_dependencies.py`**: A helper script that runs at the very beginning to ensure you have the required Python packages (`selenium`, `pytz`, `google-api-python-client`, etc.) installed and up to date.
- **`parser.py`**: A helper module that converts the Dutch date and time text from Datumprikker (e.g., "maandag 12 mei 14:00 - 15:00") into Python datetime objects.
- **`script.py`**: The main script. It first fetches your events from Google Calendar. Then, it uses Selenium to open Datumprikker, loops over the proposed times, uses `parser.py` to understand them, and checks them against your calendar. Finally, it clicks the corresponding "Yes" or "No" buttons and fills in your name and email.
