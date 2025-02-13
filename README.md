# YouTube Analytics Desktop

Project Summary: https://www.linkedin.com/in/mj-yuan-786678324/details/projects/
A desktop-style GUI tool for analyzing YouTube channel data using the YouTube Analytics API. This application provides a user-friendly interface built with Tkinter, allowing you to run analytics and view both log outputs and embedded Matplotlib plots.
![Application Screenshot](screenshot.png)
## Features

- **Desktop GUI**: Uses Tkinter's `PanedWindow` to create a two-part interface:
  - **Top Pane**: Displays log messages and control buttons using a `ScrolledText` widget.
  - **Bottom Pane**: Provides a scrollable canvas for embedded Matplotlib plots.
- **Mouse Wheel Scrolling**: Enables smooth mouse wheel scrolling over the canvas area on Windows.
- **YouTube API Integration**: Fetches channel and video analytics using the YouTube Analytics API and YouTube Data API.
- **Data Visualization**: Generates bar charts, heatmaps, scatterplots, and regression plots using Matplotlib and Seaborn.
- **Dynamic Updates**: Clears previous plots and logs on each run to provide fresh analytics output.

## Requirements

Install the following Python packages before running the application:

```bash
pip install google-auth-oauthlib google-api-python-client pycountry matplotlib seaborn isodate Pillow
```

## Setup and Usage
1. Download Files
- Place the youtube_analytics_desktop.py file and your client_secret_....json file (OAuth client secret file) in the same folder.

2. Run the Application
- Windows: Double-click youtube_analytics_desktop.py
- Terminal/Command Prompt:
```bash
python youtube_analytics_desktop.py
```

3. Using the Tool
- Click the Run Analytics button to initiate the OAuth flow, fetch YouTube analytics data, generate logs, and embed the generated plots into the scrollable area.
- Use the Quit button to exit the application.

## How It Works
1. OAuth Authentication:
- The app uses google-auth-oauthlib to authenticate with the YouTube and YouTube Analytics APIs. A local server is spun up during the OAuth flow for secure authentication.

2. Data Retrieval and Visualization:
- Channel Information: Retrieves and displays channel details such as title, subscriber count, and total views.
- Country-Level Analytics: Fetches country-based metrics (views, likes, comments, watch time) and generates bar charts.
- Video-Level Analytics: Collects detailed metrics for individual videos, computes correlation matrices, and visualizes relationships (e.g., video duration vs. views).
- Day-of-Week Analysis: Analyzes day-level data for the first week after video release and identifies optimal posting days based on view counts.

3. Embedding Plots:
- Matplotlib figures are saved as PNG files and embedded into the Tkinter canvas using Pillow's ImageTk.PhotoImage.

4. User Interface:
- The GUI is split into two main sections:
  - Top Pane: Logs and control buttons.
  - Bottom Pane: A scrollable canvas where plots are dynamically added.
  - Mouse wheel scrolling is enabled when the cursor is over the plot area on Windows systems.

## File Structure
```bash
youtube-analytics-desktop/
├── client_secret_xxxxx.json  # Your OAuth client secret file (rename as needed)
├── youtube_analytics_desktop.py  # Main Python script for the desktop app
└── README.md                  # This file
```

## Troubleshooting
1. OAuth Issues:
- Ensure that your client secret JSON file is correctly named and located in the same directory as the script.

2. API Quotas/Errors:
- If you encounter errors related to the YouTube API, verify your API quota and ensure that the correct scopes are enabled in your Google Cloud project.

3. GUI Issues on Non-Windows Platforms:
- The mouse wheel scrolling behavior is optimized for Windows. If you're using a different OS, you may need to adjust the mouse event bindings.

## License
- This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
- Google APIs Client Library for Python
- Matplotlib
- Seaborn
- Tkinter
- Pillow (PIL Fork)
