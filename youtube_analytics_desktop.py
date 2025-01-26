"""
youtube_analytics_desktop.py

A desktop-style GUI using Tkinter PanedWindow.
Top half: Logs + Buttons (ScrolledText)
Bottom half: Scrollable Canvas for embedded Matplotlib plots.

Mouse wheel scrolling is enabled in the bottom area
(when hovering over the canvas) on Windows.

Requirements:
  pip install google-auth-oauthlib google-api-python-client pycountry matplotlib seaborn isodate Pillow

Usage:
  1) Place this .py file and your client_secret_....json in the same folder.
  2) Double-click (Windows) or run via terminal: python youtube_analytics_desktop.py
  3) Click "Run Analytics" to fetch data, produce logs, and embed plots in scrollable area.
"""

import tkinter as tk
from tkinter import scrolledtext
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import pycountry
import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend for embedding
import matplotlib.pyplot as plt
import seaborn as sns
import isodate
from PIL import Image, ImageTk

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

embedded_images = []  # keep references
plot_count = 0

# ------------------- REDIRECT PRINTS -------------------
class TextRedirector:
    def __init__(self, text_widget: scrolledtext.ScrolledText):
        self.text_widget = text_widget

    def write(self, msg):
        self.text_widget.insert(tk.END, msg)
        self.text_widget.see(tk.END)  # auto-scroll

    def flush(self):
        pass

# ------------------- HELPER FUNCTIONS -------------------
def get_country_name(code):
    try:
        country = pycountry.countries.get(alpha_2=code)
        return country.name if country else code
    except:
        return code

def chunk_list(lst, chunk_size=50):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def fetch_day_level_data_for_videos(youtube_analytics, video_ids, start_date, end_date):
    all_rows = []
    for vid in video_ids:
        req = youtube_analytics.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="views",
            dimensions="day",
            filters=f"video=={vid}",
            maxResults=3650
        )
        resp = req.execute()
        if "rows" not in resp:
            continue
        cols = [h["name"] for h in resp["columnHeaders"]]
        for row in resp["rows"]:
            row_dict = dict(zip(cols, row))
            row_dict["video"] = vid
            all_rows.append(row_dict)
    df_day = pd.DataFrame(all_rows)
    if not df_day.empty:
        df_day["day"] = pd.to_datetime(df_day["day"], errors="coerce")
        df_day["views"] = pd.to_numeric(df_day["views"], errors="coerce")
    return df_day

def embed_current_matplotlib_figure(plots_frame):
    global plot_count, embedded_images
    plot_count += 1
    filename = f"plot_{plot_count}.png"

    # Save figure to PNG
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()

    # Load with Pillow
    img = Image.open(filename)
    tk_img = ImageTk.PhotoImage(img)
    embedded_images.append(tk_img)  # preserve reference

    lbl = tk.Label(plots_frame, image=tk_img)
    lbl.pack(pady=5)

# ------------------- MAIN ANALYTICS CODE -------------------
def run_youtube_analytics(plots_frame):
    # 1) OAuth
    # Replace 'your_client_secret_file.json' with the actual file name of your OAuth client secret JSON file
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret_xxxxx.json',
        SCOPES
    )
    credentials = flow.run_local_server(port=0)

    youtube = build('youtube', 'v3', credentials=credentials)
    youtube_analytics = build('youtubeAnalytics', 'v2', credentials=credentials)

    # 2) Channel Info
    channel_resp = youtube.channels().list(part='snippet,statistics', mine=True).execute()
    if channel_resp.get('items'):
        ch_info = channel_resp['items'][0]
        title = ch_info['snippet']['title']
        subs = ch_info['statistics']['subscriberCount']
        channel_views = ch_info['statistics']['viewCount']

        print("===== CHANNEL INFO =====")
        print("Channel Title:", title)
        print("Subscribers:", subs)
        print("Total Channel Views:", channel_views)
        print("========================\n")

    # 3) Country-Level
    end_date = datetime.today()
    start_date_str = "2000-01-01"
    end_date_str = end_date.strftime('%Y-%m-%d')

    req = youtube_analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date_str,
        endDate=end_date_str,
        metrics="views,likes,comments,estimatedMinutesWatched",
        dimensions="country",
        sort="-views",
        maxResults=200
    )
    resp = req.execute()

    if 'rows' not in resp:
        print("No analytics data found (country-level).")
        return

    cols = [h["name"] for h in resp["columnHeaders"]]
    data_rows = [dict(zip(cols, row)) for row in resp["rows"]]
    df = pd.DataFrame(data_rows)
    df.rename(columns={'estimatedMinutesWatched': 'watchTime'}, inplace=True)

    numeric_cols = ['views', 'likes', 'comments', 'watchTime']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.fillna(0, inplace=True)
    df['country_name'] = df['country'].apply(get_country_name)

    print("===== RAW COUNTRY ANALYTICS (first 5 rows) =====")
    print(df.head().to_string(index=False))
    print("===============================\n")

    df['likes_per_1000_views'] = np.where(
        df['views']>0, df['likes']*1000.0/df['views'], 0
    )

    # Top 5 by TOTAL LIKES
    top_5_likes = df.nlargest(5, 'likes').copy()
    print("===== TOP 5 COUNTRIES BY TOTAL LIKES =====")
    print(top_5_likes[['country_name', 'views', 'likes', 'comments', 'watchTime']].to_string(index=False))
    print("==========================================\n")

    plt.figure(figsize=(8, 5))
    plt.bar(top_5_likes['country_name'], top_5_likes['likes'], color='purple')
    plt.title("Top 5 Countries by Total Likes (Lifetime)")
    plt.xticks(rotation=45, ha='right')
    embed_current_matplotlib_figure(plots_frame)

    # Top 5 by LIKES/1000 VIEWS
    top_5_ratio = df.nlargest(5, 'likes_per_1000_views').copy()
    print("===== TOP 5 COUNTRIES (LIKES/1000 VIEWS) =====")
    print(top_5_ratio[['country_name', 'views', 'likes', 'likes_per_1000_views']].to_string(index=False))
    print("=============================================\n")

    plt.figure(figsize=(8, 5))
    plt.bar(top_5_ratio['country_name'], top_5_ratio['likes_per_1000_views'], color='skyblue')
    plt.title("Top 5 Countries by Likes per 1,000 Views (Lifetime)")
    plt.xticks(rotation=45, ha='right')
    embed_current_matplotlib_figure(plots_frame)

    # Top 5 by COMMENTS
    top_5_comments = df.nlargest(5, "comments").copy()
    print("===== TOP 5 COUNTRIES BY TOTAL COMMENTS =====")
    print(top_5_comments[['country_name', 'views', 'likes', 'comments', 'watchTime']].to_string(index=False))
    print("=============================================\n")

    plt.figure(figsize=(8, 5))
    plt.bar(top_5_comments["country_name"], top_5_comments["comments"], color='orchid')
    plt.title("Top 5 Countries by Total Comments (Lifetime)")
    plt.xticks(rotation=45, ha='right')
    embed_current_matplotlib_figure(plots_frame)

    # Top 5 by COMMENTS per 50,000 views
    df["comments_per_50000_views"] = np.where(
        df["views"]>0, df["comments"] * 50000.0 / df["views"], 0
    )
    top_5_cpv = df.nlargest(5, "comments_per_50000_views").copy()
    print("===== TOP 5 COUNTRIES (COMMENTS/50,000 VIEWS) =====")
    print(top_5_cpv[['country_name', 'views', 'comments', 'comments_per_50000_views']].to_string(index=False))
    print("=======================================================\n")

    plt.figure(figsize=(8, 5))
    plt.bar(top_5_cpv["country_name"], top_5_cpv["comments_per_50000_views"], color='magenta')
    plt.title("Top 5 Countries by Comments per 50,000 Views (Lifetime)")
    plt.xticks(rotation=45, ha='right')
    embed_current_matplotlib_figure(plots_frame)

    # ----------------- VIDEO-LEVEL --------------------
    print("===== VIDEO-LEVEL ANALYSIS & CORRELATIONS =====")
    video_request = youtube_analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date_str,
        endDate=end_date_str,
        metrics="views,likes,comments,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,shares",
        dimensions="video",
        sort="-views",
        maxResults=200
    )
    video_response = video_request.execute()

    if 'rows' not in video_response:
        print("No video-level data found.")
        return

    vid_cols = [h["name"] for h in video_response["columnHeaders"]]
    vid_rows = [dict(zip(vid_cols, r)) for r in video_response["rows"]]

    df_video = pd.DataFrame(vid_rows)
    df_video.rename(columns={
        'estimatedMinutesWatched': 'watchTime',
        'averageViewDuration': 'avgViewDur',
        'averageViewPercentage': 'avgViewPct'
    }, inplace=True)
    video_numeric_cols = ['views','likes','comments','watchTime','avgViewDur','avgViewPct','shares']
    for c in video_numeric_cols:
        df_video[c] = pd.to_numeric(df_video[c], errors='coerce')
    df_video.fillna(0, inplace=True)

    print("\n--- VIDEO-LEVEL DATA (first 5 rows) ---")
    print(df_video.head().to_string(index=False))

    corr_matrix = df_video[video_numeric_cols].corr(method='pearson')
    print("\n--- CORRELATION MATRIX (PEARSON) ---")
    print(corr_matrix)

    plt.figure(figsize=(8, 6))
    sns.heatmap(corr_matrix, annot=True, cmap='Blues', fmt=".2f", square=True)
    plt.title("Correlation Heatmap (Video-Level Metrics)")
    embed_current_matplotlib_figure(plots_frame)

    # Relationship: Video Duration
    print("\n===== RELATIONSHIP BETWEEN VIDEO DURATION AND INTERACTIONS =====")
    video_ids = df_video["video"].unique().tolist()
    durations = []
    for chunk in chunk_list(video_ids, 50):
        detail_response = youtube.videos().list(
            part="contentDetails",
            id=",".join(chunk)
        ).execute()
        for item in detail_response.get("items", []):
            vid_id = item["id"]
            dur_str = item["contentDetails"]["duration"]
            td = isodate.parse_duration(dur_str)
            duration_seconds = td.total_seconds()
            durations.append({"video": vid_id, "duration_sec": duration_seconds})

    df_dur = pd.DataFrame(durations)
    df_video = pd.merge(df_video, df_dur, on="video", how="left")

    # Only <= 30 min
    df_video = df_video[df_video["duration_sec"] <= 1800]
    interaction_cols = ["views","likes","comments","shares"]
    corr_with_duration = df_video[interaction_cols+["duration_sec"]].corr()
    print("\n--- CORRELATION WITH VIDEO DURATION (<= 30 MINUTES) ---")
    print(corr_with_duration["duration_sec"].sort_values(ascending=False))

    plt.figure(figsize=(8,6))
    sns.scatterplot(data=df_video, x="duration_sec", y="views")
    plt.title("Video Duration (<=30 min) vs. Views")
    embed_current_matplotlib_figure(plots_frame)

    plt.figure(figsize=(8,6))
    sns.regplot(data=df_video, x="duration_sec", y="views", scatter_kws={"alpha": 0.5})
    plt.title("Video Duration (<=30 min) vs. Views (Regression)")
    embed_current_matplotlib_figure(plots_frame)

    plt.figure(figsize=(8,6))
    sns.scatterplot(data=df_video, x="duration_sec", y="likes", color='orange')
    plt.title("Video Duration (<=30 min) vs. Likes")
    embed_current_matplotlib_figure(plots_frame)

    # DAY-OF-WEEK
    print("\n===== DAY-OF-WEEK ANALYSIS (FIRST 7 DAYS AFTER RELEASE) =====")
    df_day_video = fetch_day_level_data_for_videos(
        youtube_analytics, video_ids, start_date_str, end_date_str
    )
    if df_day_video.empty:
        print("No day-level data returned.")
        return

    snippet_data = []
    for chunk in chunk_list(video_ids, 50):
        detail_snippet = youtube.videos().list(
            part="snippet",
            id=",".join(chunk)
        ).execute()
        for item in detail_snippet.get("items", []):
            vid_id = item["id"]
            pub_str = item["snippet"]["publishedAt"]
            pub_dt = datetime.strptime(pub_str, "%Y-%m-%dT%H:%M:%SZ")
            snippet_data.append({"video": vid_id, "publish_datetime": pub_dt})

    df_snippet = pd.DataFrame(snippet_data)
    df_day_video = pd.merge(df_day_video, df_snippet, on="video", how="left")

    df_day_video["elapsed_days"] = (df_day_video["day"] - df_day_video["publish_datetime"]).dt.days
    df_first_week = df_day_video.loc[
        (df_day_video["elapsed_days"]>=0) & (df_day_video["elapsed_days"]<7)
    ].copy()
    df_first_week["day_gmt_minus_5"] = df_first_week["day"] - timedelta(hours=5)
    df_first_week["day_of_week_gmt_minus_5"] = df_first_week["day_gmt_minus_5"].dt.strftime("%A")

    grouped = df_first_week.groupby("day_of_week_gmt_minus_5")["views"].sum().reset_index()
    grouped = grouped.sort_values(by="views", ascending=False)
    print("\nViews by Day of Week (GMT -0500), first 7 days after release:\n")
    print(grouped.to_string(index=False))

    if not grouped.empty:
        best_day = grouped.iloc[0]["day_of_week_gmt_minus_5"]
        best_day_views = grouped.iloc[0]["views"]
        print(f"\n** Best day (GMT -0500) for first-7-day views: {best_day} **")
        print(f"(Total {int(best_day_views)} views in first 7 days)\n")
    else:
        print("No data in first 7 days.\n")

    plt.figure(figsize=(8,5))
    plt.bar(grouped["day_of_week_gmt_minus_5"], grouped["views"], color='green')
    plt.title("Views by Day of Week (GMT -0500)\nFirst 7 Days After Release")
    embed_current_matplotlib_figure(plots_frame)

# ------------------- GUI CODE -------------------
def create_gui():
    root = tk.Tk()
    root.title("YouTube Analytics Tool - Mouse Wheel Scroll")
    root.geometry("1000x800")

    # PanedWindow (vertical)
    pane = tk.PanedWindow(root, orient=tk.VERTICAL)
    pane.pack(fill=tk.BOTH, expand=True)

    # (1) TOP pane
    top_frame = tk.Frame(pane)
    pane.add(top_frame, stretch="always")

    # layout top_frame in grid
    top_frame.grid_rowconfigure(1, weight=1)  # text area expands
    top_frame.grid_columnconfigure(0, weight=1)

    button_frame = tk.Frame(top_frame)
    button_frame.grid(row=0, column=0, sticky="nw", pady=5)

    text_area = scrolledtext.ScrolledText(top_frame, wrap=tk.WORD)
    text_area.grid(row=1, column=0, sticky="nsew")

    # (2) BOTTOM pane
    bottom_frame = tk.Frame(pane)
    pane.add(bottom_frame, stretch="always")

    plots_canvas = tk.Canvas(bottom_frame)
    plots_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scroll_y = tk.Scrollbar(bottom_frame, orient='vertical', command=plots_canvas.yview)
    scroll_y.pack(side=tk.RIGHT, fill='y')

    plots_canvas.configure(yscrollcommand=scroll_y.set)
    plots_frame = tk.Frame(plots_canvas)
    plots_canvas.create_window((0, 0), window=plots_frame, anchor='nw')

    def on_plots_frame_configure(event):
        plots_canvas.configure(scrollregion=plots_canvas.bbox("all"))
    plots_frame.bind("<Configure>", on_plots_frame_configure)

    # ============================
    # MOUSE WHEEL SCROLL (WINDOWS)
    # ============================
    def _on_mousewheel(event):
        # event.delta is typically ±120 on Windows
        plots_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # Bind mouse wheel *when pointer is over the canvas*
    # Unbind when it leaves (so we don't scroll everything in the app).
    def _bind_to_mousewheel(_event):
        plots_canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_from_mousewheel(_event):
        plots_canvas.unbind_all("<MouseWheel>")

    plots_canvas.bind("<Enter>", _bind_to_mousewheel)
    plots_canvas.bind("<Leave>", _unbind_from_mousewheel)

    # Redirect stdout to text_area
    redir = TextRedirector(text_area)
    sys.stdout = redir

    # RUN button
    def on_run_click():
        text_area.delete('1.0', tk.END)
        for w in plots_frame.winfo_children():
            w.destroy()
        embedded_images.clear()
        global plot_count
        plot_count = 0

        print("Starting YouTube Analytics...\n")
        run_youtube_analytics(plots_frame)
        print("Finished Analytics.\n")

    run_btn = tk.Button(button_frame, text="Run Analytics", command=on_run_click)
    run_btn.pack(side=tk.LEFT, padx=5)

    quit_btn = tk.Button(button_frame, text="Quit", command=root.destroy)
    quit_btn.pack(side=tk.LEFT, padx=5)

    root.mainloop()

if __name__ == '__main__':
    create_gui()
