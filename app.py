from webbrowser import Mozilla

import streamlit as st
import yt_dlp
import os

st.set_page_config(page_title="Video Downloader", page_icon="🎬")
st.title("🎬 Video Downloader")

url = st.text_input("enter video url")

try:
    st.video(url,width=500)
except:
    video_id = url.split("v=")[-1] if "v=" in url else url.split("/")[-1]
    thumbnail = f"https://img.youtube.com/vi/{video_id}/0.jpg"
    
    st.image(thumbnail)
    st.link_button("Watch on YouTube", url)

format = st.selectbox("choose format:",["mp4","webm"])

# If mp3 chosen, add postprocessor and skip quality selection
if format == "mp3":
    ydl_format = "bestaudio/best"
    postprocessors = [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
    mime_type = "audio/mpeg"

else:
    # Ask user for quality only if video format
    quality_choice = st.selectbox("Choose video quality:",["Best available","1080p","720p","480p"])
    
    if quality_choice == "Best available":
        ydl_format = "best"
    elif quality_choice == "1080p":
        ydl_format = "best[height<=1080]"
    elif quality_choice == "720p":
        ydl_format = "best[height<=720]"
    elif quality_choice == "480p":
        ydl_format = "best[height<=480]"
    postprocessors = []
    mime_type = "video/mp4"

# temp file name
output_file = "%(title)s.%(ext)s"

ydl_opts = {
        'format': ydl_format,                # always video+audio if video selected
        'outtmpl': output_file,   # final file format
        'postprocessors': postprocessors,
        'max_filesize': 50 * 1024 * 1024,   # 50 MB limit
        'merge_output_format': format if format == "mp4" else None,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        }
    } 

if st.button("Download"):
    if url:
        try:
            with st.spinner("Downloading..."):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    file_name = ydl.prepare_filename(info)
                    if format == "mp3":
                        file_name = os.path.splitext(file_name)[0] + ".mp3"

            # Read file
            with open(file_name, "rb") as f:
                file_bytes = f.read()

            # Show download button
            st.download_button(
                label="Download file",
                data=file_bytes,
                file_name=os.path.basename(file_name),
                mime= mime_type
            )
            st.success("Ready to download!")

        except Exception as e:
            st.error(f"❌ Download error: {e}")
    else:
        st.warning("Please enter a valid URL")

