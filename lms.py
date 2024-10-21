import os
import json
from googleapiclient.discovery import build
import streamlit as st
import isodate

# Get the API key from environment variable
api_key = os.getenv('YOUTUBE_API_KEY')

# Initialize YouTube API client
youtube = build('youtube', 'v3', developerKey=api_key)

def get_playlist_videos(playlist_id):
    videos = []
    next_page_token = None

    while True:
        # Fetch playlist items (videos)
        playlist_response = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        # Iterate over each video in the playlist
        for item in playlist_response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            video_title = item['snippet']['title']
            videos.append({'title': video_title, 'id': video_id})

        # Check if there's a next page
        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break
    
    return videos

def get_video_duration(video_id):
    video_response = youtube.videos().list(
        part="contentDetails",
        id=video_id
    ).execute()
    
    duration = video_response['items'][0]['contentDetails']['duration']
    return isodate.parse_duration(duration).total_seconds()

def get_video_description(video_id):
    video_response = youtube.videos().list(
        part="snippet",
        id=video_id
    ).execute()
    
    return video_response['items'][0]['snippet']['description']

def format_duration(seconds):
    """Format duration in seconds to 'HH:MM'."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

def load_completed_videos(filename='completed_videos.json'):
    """Load completed videos from a JSON file."""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def save_completed_videos(completed_videos, filename='completed_videos.json'):
    """Save completed videos to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(completed_videos, f)

# Replace with your playlist ID
playlist_id = 'PLPTV0NXA_ZSj6tNyn_UadmUeU3Q3oR-hu'

# Fetch videos from the playlist
video_list = get_playlist_videos(playlist_id)

# Fetch video durations and total duration of the course
total_duration = 0
for video in video_list:
    duration = get_video_duration(video['id'])
    video['duration'] = duration
    total_duration += duration

# Streamlit UI Layout
st.set_page_config(layout="wide")  # Set page to wide layout

# Load completed videos from file
if 'completed_videos' not in st.session_state:
    st.session_state.completed_videos = load_completed_videos()

# Sidebar - Completion Summary at the Top
st.sidebar.header("Completion Summary")

completed_videos = st.session_state.completed_videos

st.sidebar.write(f"Completed {len(completed_videos)} out of {len(video_list)} videos.")

completed_duration = sum(video['duration'] for video in video_list if video['title'] in completed_videos)
remaining_duration = total_duration - completed_duration

st.sidebar.write(f"Total Duration: {format_duration(total_duration)}")
st.sidebar.write(f"Completed: {format_duration(completed_duration)}")
st.sidebar.write(f"Remaining: {format_duration(remaining_duration)}")

if total_duration > 0:
    progress = (completed_duration / total_duration) * 100
else:
    progress = 0

st.sidebar.progress(progress / 100)
st.sidebar.write(f"Progress: {progress:.2f}%")

# Sidebar - Video Playlist Below Completion Summary
st.sidebar.header("Playlist")
for i, video in enumerate(video_list):
    checkbox_value = video['title'] in completed_videos
    if st.sidebar.checkbox(f"{video['title']} - {format_duration(video['duration'])}", value=checkbox_value, key=f"video_{i}"):
        if video['title'] not in completed_videos:
            completed_videos.append(video['title'])
            save_completed_videos(completed_videos)  # Save to file when checked
    else:
        if video['title'] in completed_videos:
            completed_videos.remove(video['title'])
            save_completed_videos(completed_videos)  # Save to file when unchecked

# Main content - Embed selected video
st.header("Learning Progress Tracker")
selected_video = st.selectbox("Choose a video to play", options=video_list, format_func=lambda video: video['title'])
st.write(f"Now Playing: {selected_video['title']}")
    
# Embed the video with 1920x1080 resolution using HTML
video_url = f"https://www.youtube.com/embed/{selected_video['id']}"
st.markdown(
    f'<iframe width="1920" height="1080" src="{video_url}" frameborder="0" allowfullscreen></iframe>',
    unsafe_allow_html=True
)
    
# Fetch and display video description
description = get_video_description(selected_video['id'])
st.subheader("Description")
st.write(description)

# Optional: Add any extra styling or spacing
st.write("")
