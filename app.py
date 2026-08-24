import requests
import streamlit as st

st.set_page_config(page_title="Video Downloader", page_icon="🎬")

# Change this after deploying the FastAPI backend.
DEFAULT_API_URL = "http://localhost:8000"

page_bg_img = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: url("https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fimg.freepik.com%2Fphotos-gratuite%2Fabstrait-numerique-grille-fond-noir_53876-97647.jpg%3Fsemt%3Dais_hybrid%26w%3D740&f=1");
    background-size: cover;
}
[data-testid="stHeader"] {
    background-color: rgba(0, 0, 0, 0);
}
</style>
"""

st.markdown(page_bg_img, unsafe_allow_html=True)

API_URL = st.secrets["BACKEND_URL"].rstrip("/")

with st.sidebar:
    st.subheader("ℹ️ About this app")
    st.write(
        "This demo separates the Streamlit frontend from the FastAPI "
        "backend that runs yt-dlp."
    )
    st.markdown(
        "### 📌 How to use:\n"
        "1. Paste a video URL\n"
        "2. Load available qualities\n"
        "3. Select format and quality\n"
        "4. Download"
    )

st.title("🎬 Video Downloader")

col1, col2 = st.columns([3, 2])

url = col1.text_input("Enter video URL")

if url:
    if url.startswith(("https://", "http://")):
        if "youtube.com" in url or "youtu.be" in url:
            col2.video(url)
        else:
            col2.info("Preview not available for this platform.")
            col2.link_button("Open Video", url)
    else:
        col1.error("Please enter a valid video URL.")

if "qualities" not in st.session_state:
    st.session_state.qualities = ["Best available"]
if "video_info" not in st.session_state:
    st.session_state.video_info = None
if "last_url" not in st.session_state:
    st.session_state.last_url = ""

if url and url != st.session_state.last_url:
    st.session_state.qualities = ["Best available"]
    st.session_state.video_info = None

if col1.button("Load available qualities", disabled=not url):
    try:
        with col1.spinner("Checking video information..."):
            response = requests.post(
                f"{API_URL}/info",
                json={"url": url},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

        qualities = ["Best available"]
        for quality in data.get("qualities", []):
            if quality not in qualities:
                qualities.append(quality)

        st.session_state.qualities = qualities
        st.session_state.video_info = data
        st.session_state.last_url = url

    except requests.RequestException as exc:
        col2.error(f"Backend error: {exc}")

info = st.session_state.video_info
file_name="video"

if info:
    file_name=info.get("title")
    col2.success(info.get("title", "Video found"))

    filesize = info.get("filesize")
    if filesize:
        col2.info(f"📦 Estimated size: {filesize / (1024 * 1024):.2f} MB")
    else:
        col2.warning("⚠️ Unable to determine file size.")

format_choice = col1.selectbox("Choose format", ["mp4", "webm", "mp3"])

qualities = st.session_state.qualities.copy()
if format_choice == "mp3":
    quality_choice = "Best available"
    col1.info("MP3 uses the best available audio stream.")
else:
    video_qualities = [q for q in qualities if q != "mp3"]
    quality_choice = col1.selectbox("Choose video quality", video_qualities)

if col1.button("Download", disabled=not url):
    try:
        with col1.spinner("Downloading from backend... This may take a while."):
            response = requests.post(
                f"{API_URL}/download",
                json={
                    "url": url,
                    "format": format_choice,
                    "quality": quality_choice,
                },
                timeout=600,
            )

        if not response.ok:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            st.error(f"❌ Download error: {detail}")
        else:
            content_disposition = response.headers.get("content-disposition", "")
            filename = f"video.{format_choice}"

            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=", 1)[1].strip('"')

            mime_type = (
                "audio/mpeg"
                if format_choice == "mp3"
                else "video/mp4"
                if format_choice == "mp4"
                else "video/webm"
            )

            col1.download_button(
                label="Save downloaded file",
                data=response.content,
                file_name=file_name,
                mime=mime_type,
            )
            col1.success("Ready to save!")

    except requests.Timeout:
        col2.error("❌ The backend timed out while downloading the video.")
    except requests.RequestException as exc:
        col2.error(f"❌ Backend connection error: {exc}")
