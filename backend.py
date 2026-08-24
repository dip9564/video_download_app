import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Literal

from requests import request
import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from starlette.background import BackgroundTask

app = FastAPI(title="Video Downloader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to your Streamlit domain in production.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VideoInfoRequest(BaseModel):
    url: HttpUrl


class DownloadRequest(BaseModel):
    url: HttpUrl
    format: Literal["mp4", "webm", "mp3"] = "mp4"
    quality: str = "Best available"


def clean_formats(info: dict) -> list[str]:
    qualities = []
    seen = set()
    audio_added = False

    for f in info.get("formats", []):
        ext = f.get("ext")
        if ext in ("mhtml", None, "webm"):
            continue

        height = f.get("height")
        if height:
            quality = f"{height}p"
        elif not audio_added:
            quality = "mp3"
            audio_added = True
        else:
            continue

        if quality not in seen:
            seen.add(quality)
            qualities.append(quality)

    return qualities


def get_video_format(quality: str) -> str:
    if quality == "Best available":
        return (
            "bestvideo[vcodec^=avc1][ext=mp4]"
            "+bestaudio[acodec^=mp4a]"
            "/best[ext=mp4][vcodec^=avc1]"
            "/best"
        )

    match = re.match(r"(\d+)p$", quality)

    if not match:
        return (
            "bestvideo[vcodec^=avc1][ext=mp4]"
            "+bestaudio[acodec^=mp4a]"
            "/best[ext=mp4][vcodec^=avc1]"
            "/best"
        )

    height = int(match.group(1))

    return (
        f"bestvideo[vcodec^=avc1][height<={height}][ext=mp4]"
        f"+bestaudio[acodec^=mp4a]"
        f"/best[ext=mp4][height<={height}][vcodec^=avc1]"
        "/best"
    )

def base_ydl_options(output_template: str) -> dict:
    return {
        "outtmpl": output_template,
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 10,
        # Requires Deno to be installed on the backend environment.
        "js_runtimes": {"deno": {}},
        "remote_components": {"ejs:github"},
    }


@app.get("/")
def root():
    return {"message": "Video Downloader API is running"}


@app.post("/info")
def video_info(request: VideoInfoRequest):
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(str(request.url), download=False)

        filesize = info.get("filesize") or info.get("filesize_approx")

        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "filesize": filesize,
            "qualities": clean_formats(info),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/download")
def download_video(request: DownloadRequest):
    temp_dir = Path(tempfile.mkdtemp(prefix="video_downloader_"))
    output_template = str(temp_dir / "%(title)s.%(ext)s")

    try:
        if request.format == "mp3":
            ydl_format = "bestaudio/best"
        
            postprocessors = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        
            merge_output_format = None
            media_type = "audio/mpeg"
        
        else:
            ydl_format = get_video_format(request.quality)
        
            postprocessors = []
        
            merge_output_format = request.format
        
            media_type = (
                "video/mp4"
                if request.format == "mp4"
                else "video/webm"
            )

        ydl_opts = base_ydl_options(output_template)
        ydl_opts.update({
            "format": ydl_format,
            "postprocessors": postprocessors,
            "merge_output_format": merge_output_format,
        })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(str(request.url), download=True)
            downloaded_file = Path(ydl.prepare_filename(info))

        if request.format == "mp3":
            downloaded_file = downloaded_file.with_suffix(".mp3")

        if not downloaded_file.exists():
            files = list(temp_dir.glob("*"))
            if not files:
                raise FileNotFoundError("yt-dlp did not create an output file.")
            downloaded_file = files[0]

        safe_name = downloaded_file.name

        return FileResponse(
            path=downloaded_file,
            media_type=media_type,
            filename=safe_name,
            background=BackgroundTask(shutil.rmtree, temp_dir, ignore_errors=True),
        )

    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(exc))
