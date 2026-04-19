from webbrowser import Mozilla

import streamlit as st
import yt_dlp
import os

st.set_page_config(page_title="Video Downloader", page_icon="🎬")
st.title("🎬 Video Downloader")

url = st.text_input("enter video url")

if url:
    if "youtube.com" in url or "youtu.be" in url:
        st.video(url,width=500)
    else:
        st.info("Preview not available for this platform")
        st.video(url)
        st.link_button("Open Video", url)

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
        'merge_output_format': format if format == "mp4" else None,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        }
    } 

if st.button("Download"):
    if url:
        try:
            with st.spinner("Checking video..."):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            
            filesize = info.get("filesize") or info.get("filesize_approx")
            if filesize:
                st.info(f"📦 File size: {filesize / (1024*1024):.2f} MB")
            else:
                st.warning("⚠️ Unable to determine file size.")

            if filesize and filesize > 70 * 1024 * 1024:
                st.error("❌ File size is greater than 70MB")
                st.stop()

            with st.spinner("Downloading..."):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    file_name = ydl.prepare_filename(info)

            # Read file
            with open(file_name, "rb") as f:
                file_bytes = f.read(70 * 1024 * 1024)  # read up to 70MB

            # Show download button
            st.download_button(
                label="Download file",
                data=file_bytes,
                file_name=os.path.basename(file_name),
                mime= mime_type
            )
            st.success("Ready to download!")

            if os.path.exists(file_name):
                os.remove(file_name)

        except Exception as e:
            st.error(f"❌ Download error: {e}")
    else:
        st.warning("Please enter a valid URL")

# sidebar 
with st.sidebar:
    st.subheader("ℹ️ About this app")
    st.write("This app is created by 'Dip Mondal'.")
    st.write(
             "It is a demo project for learning streamlit and yt-dlp"
             )
    st.write(
        "This app allows you to download videos from supported platforms like facebook, twitter, instagram."
        "In different formats and qualities."
    )
    st.markdown("### 📌 How to use:")
    st.write(
        "1. Paste a video URL\n"
        "2. Select format and quality\n"
        "3. Click Download\n"
        "4. Save the file"
    )
    st.warning("⚠️ Large videos may not work on cloud version. File size less than 100MB")