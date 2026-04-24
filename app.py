import streamlit as st
import yt_dlp
import os, re

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

# main app
st.set_page_config(page_title="Video Downloader", page_icon="🎬")
st.title("🎬 Video Downloader")

def clean_text(text):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

def progress_hook(d, progress_bar, status_text):
    
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)

        if total:
            progress = downloaded / total
            progress_bar.progress(min(progress, 1.0))

        speed =clean_text(d.get('_speed_str', ''))
        eta = clean_text(d.get('_eta_str', ''))

        status_text.text(f"Downloading... {int(progress*100)}% | {speed} | ETA: {eta}")

    elif d['status'] == 'finished':
        progress_bar.progress(1.0)
        status_text.text("Processing file...")

def show_formats(url):
    """Fetch and display available formats in a clean way"""
    qualitys=[]
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        seen = set()
        audio_add=True
        for f in info.get('formats', []):
            ext = f.get('ext')
            if ext in ["mhtml", None,"webm"]:  # skip storyboards/thumbnails and webm
                continue

            flag=True
            if f.get("height"):
                res = f"{f['height']}p"
            else:
                if audio_add:
                    res = "mp3"
                    audio_add=False
            if res in qualitys:
                continue
            key = (res, ext)
            if key in seen:
                continue
            seen.add(key)
            qualitys.append(res)

    st.info(f"Available formats : {qualitys}")

    return qualitys

url_check=None
url = st.text_input("enter video url")
quality=['Best available']

if url:
    if "https:" in url :
        if "youtube.com" in url or "youtu.be" in url:
            st.video(url,width=500)
        else:
            st.info("Preview not available for this platform")
            st.link_button("Open Video", url)
        url_check=True
    else:
        st.error("Please enter a valid video URL")

    try:
        quality.extend( show_formats(url))
    except Exception as e:
        url_check = False

format_ls=["mp4","webm"]
if "mp3" in quality:
    format_ls.extend(["mp3"])
format = st.selectbox("choose format:",format_ls)

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
    if "mp3" in quality:
        quality.remove("mp3")
    quality_choice = st.selectbox("Choose video quality:",quality)
    
    if quality_choice in ["Best available", "4320p"]:
        ydl_format = "best"
    elif quality_choice in ["2160p","2560p","1920p"]:
        ydl_format = "best[height<=2160]"
    elif quality_choice in ["1440p","1280p","1444p"]:
        ydl_format = "best[height<=1440]"
    elif quality_choice in ["1080p", "960p", "1084p","1136p","1137p"]:
        ydl_format = "best[height<=1080]"
    elif quality_choice in ["720p", "520p", "536p", "718p", "640p", "540p"]:
        ydl_format = "best[height<=720]"
    elif quality_choice in ["480p"]:
        ydl_format = "best[height<=480]"
    elif quality_choice in ["360p", "356p"]:
        ydl_format = "best[height<=360]"
    elif quality_choice in ["240p", "144p"]:
        ydl_format = "best[height<=240]"
    else : 
        st.error("this format is not downloadable")
    postprocessors = []
    mime_type = "video/mp4"

# temp file name
output_file = "%(title)s.%(ext)s"

ydl_opts = {
        'format': ydl_format,                # always video+audio if video selected
        'outtmpl': output_file,   # final file format
        'postprocessors': postprocessors,
        'merge_output_format': format if format == "mp4" else None,
        'progress_hooks': [lambda d: progress_hook(d, progress_bar, status_text)],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        }
    } 
filesize=None
if url_check:
    try:
        with st.spinner("Checking fileSize..."):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

        filesize = info.get("filesize") or info.get("filesize_approx")
        if filesize:
            st.info(f"📦 File size: {filesize / (1024*1024):.2f} MB")
        else:
            st.warning("⚠️ Unable to determine file size.")
    except Exception as e:
        st.warning("⚠️ Unable to determine file size.")

if st.button("Download"):
    if url:
        try:
            if filesize and filesize > 70 * 1024 * 1024:
                st.error("❌ File size is greater than 70MB")
                st.stop()

            with st.spinner("Downloading..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
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
                mime= "video/mp4"
            )
            st.success("Ready to download!")

            if os.path.exists(file_name):
                os.remove(file_name)

        except Exception as e:
            st.error(f"❌ Download error: {e}")
    else:
        st.warning("Please enter a valid URL")
