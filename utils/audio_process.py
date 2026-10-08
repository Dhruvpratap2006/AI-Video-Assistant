# ---------------------------------------------------------------
#               Audio Processing
# File    : utils/audio_process.py
# Purpose : Take a YouTube link or a local file and give back small
#           WAV chunks that are ready for Whisper / Sarvam
# ---------------------------------------------------------------
#
# What this file does:
# 1. If the input is a YouTube link -> download only the audio (yt-dlp)
# 2. If the input is a local file (.mp4 .mp3 .wav .m4a) -> use it directly
# 3. Convert the audio to WAV, 16kHz, mono (this is what speech models like)
# 4. Cut the long audio into 10-minute chunks
#    (Whisper cannot handle a very long file in one go)
#
# Input : YouTube URL or local file path
# Output: list of chunk file paths, for example
#         ["video_converted_chunk_0.wav", "video_converted_chunk_1.wav"]
# ---------------------------------------------------------------

import re
from yt_dlp.utils import DownloadError
import yt_dlp
import os
import imageio_ffmpeg
from pydub import AudioSegment

# Folder where all downloaded audio and chunks are saved
DOWONOLAD_DIR = 'dowonolades'
os.makedirs(DOWONOLAD_DIR, exist_ok=True)  # create the folder if it is not there

import shutil

# Get the path of ffmpeg (check system ffmpeg first, then bundled imageio-ffmpeg)
system_ffmpeg = shutil.which("ffmpeg")
FFMPEG_PATH = system_ffmpeg or imageio_ffmpeg.get_ffmpeg_exe()

# pydub also needs to know where ffmpeg is
AudioSegment.converter = FFMPEG_PATH


def extract_youtube_video_id(url: str) -> str | None:
    """Extract standard 11-character video ID from any YouTube URL format."""
    match = re.search(r'(?:v=|\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else None


def fetch_youtube_transcript(url: str, language: str = "english") -> dict | None:
    """
    Fetch captions directly from YouTube via official transcript API.
    Bypasses audio downloading and datacenter 403 bot blocks in ~0.5s.
    """
    video_id = extract_youtube_video_id(url)
    if not video_id:
        return None

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        import requests

        session = None
        cookie_path = os.path.join(DOWONOLAD_DIR, "yt_cookies.txt") if os.path.exists(os.path.join(DOWONOLAD_DIR, "yt_cookies.txt")) else ("cookies.txt" if os.path.exists("cookies.txt") else None)
        if cookie_path:
            import http.cookiejar
            try:
                jar = http.cookiejar.MozillaCookieJar(cookie_path)
                jar.load(ignore_discard=True, ignore_expires=True)
                session = requests.Session()
                session.cookies = jar
            except Exception:
                session = None

        ytt = YouTubeTranscriptApi(http_client=session) if session else YouTubeTranscriptApi()

        # 1. Try listing transcripts and selecting preferred language
        try:
            tl = ytt.list(video_id)
            langs = ['en', 'en-US', 'en-GB'] if language.lower() == 'english' else ['hi', 'en', 'en-US']
            chosen_transcript = None
            try:
                chosen_transcript = tl.find_transcript(langs)
            except Exception:
                for t in tl:
                    chosen_transcript = t
                    break

            if chosen_transcript:
                snippets = chosen_transcript.fetch()
                if snippets:
                    segments = []
                    for s in snippets:
                        text = getattr(s, 'text', '') if hasattr(s, 'text') else s.get('text', '')
                        start = getattr(s, 'start', 0.0) if hasattr(s, 'start') else s.get('start', 0.0)
                        dur = getattr(s, 'duration', 0.0) if hasattr(s, 'duration') else s.get('duration', 0.0)
                        if text.strip():
                            segments.append({
                                "text": text.strip(),
                                "start": round(float(start), 2),
                                "end": round(float(start + dur), 2),
                            })
                    full_text = " ".join(seg["text"] for seg in segments)
                    if full_text.strip():
                        print(f"Successfully fetched YouTube transcript ({len(segments)} segments) via API.")
                        return {"text": full_text.strip(), "segments": segments}
        except Exception as e:
            print(f"[Notice] Transcript list query failed ({e}), attempting direct fetch...")

        # 2. Try direct fetch fallback
        snippets = ytt.fetch(video_id)
        if snippets:
            segments = []
            for s in snippets:
                text = getattr(s, 'text', '') if hasattr(s, 'text') else s.get('text', '')
                start = getattr(s, 'start', 0.0) if hasattr(s, 'start') else s.get('start', 0.0)
                dur = getattr(s, 'duration', 0.0) if hasattr(s, 'duration') else s.get('duration', 0.0)
                if text.strip():
                    segments.append({
                        "text": text.strip(),
                        "start": round(float(start), 2),
                        "end": round(float(start + dur), 2),
                    })
            full_text = " ".join(seg["text"] for seg in segments)
            if full_text.strip():
                print(f"Successfully fetched direct YouTube transcript ({len(segments)} segments).")
                return {"text": full_text.strip(), "segments": segments}

    except Exception as err:
        print(f"[Notice] YouTube transcript API unavailable for '{video_id}': {err}")

    return None


# Download the audio of a YouTube video and save it as a WAV file
def download_youtube_audio(url: str) -> str:
    """Download audio from YouTube using robust client emulation and cookies to bypass HTTP 403 bot blocks."""
    output_template = os.path.join(DOWONOLAD_DIR, "%(id)s.%(ext)s")

    # Check for user-provided cookies in environment (Streamlit Secrets) or local cookies.txt
    cookie_file = None
    env_cookies = os.getenv("YOUTUBE_COOKIES", "").strip()
    if not env_cookies:
        try:
            import streamlit as st
            env_cookies = str(st.secrets.get("YOUTUBE_COOKIES", "")).strip()
        except Exception:
            pass

    if env_cookies:
        temp_cookie_path = os.path.join(DOWONOLAD_DIR, "yt_cookies.txt")
        try:
            with open(temp_cookie_path, "w", encoding="utf-8") as cf:
                cf.write(env_cookies)
            cookie_file = temp_cookie_path
        except Exception:
            cookie_file = None
    elif os.path.exists("cookies.txt"):
        cookie_file = "cookies.txt"

    client_strategies = [
        ["android"],
        ["mweb", "ios"],
        ["ios", "android", "mweb"],
        ["android", "web"],
    ]

    last_error = None
    for clients in client_strategies:
        ydl_opts = {
            "format": "ba/b",                # Best audio, or best lightweight format with audio
            "outtmpl": output_template,      # Windows-safe filename using video ID
            "ffmpeg_location": FFMPEG_PATH,  # Location of ffmpeg binary
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "quiet": True,
            "no_warnings": True,
            "nopart": True,                  # Avoids Windows file locking issues
            "noplaylist": True,              # Only single video
            "windowsfilenames": True,
            "extractor_args": {
                "youtube": {
                    "player_client": clients,
                }
            },
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        if cookie_file and os.path.exists(cookie_file):
            ydl_opts["cookiefile"] = cookie_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                raw_filename = ydl.prepare_filename(info)
                filename = os.path.splitext(raw_filename)[0] + ".wav"
                if os.path.exists(filename):
                    print(f"Successfully downloaded audio using client: {clients}")
                    return filename
        except Exception as e:
            last_error = e
            print(f"[RETRY] YouTube client strategy {clients} failed: {e}. Trying alternative...")
            continue

    raise RuntimeError(
        f"YouTube rejected the download request (HTTP 403 or bot block). "
        f"YouTube frequently restricts automated stream access from cloud providers. "
        f"You can either: 1) Upload the recording directly (.mp4, .mp3, .wav) in the 'Upload File' tab, "
        f"or 2) Add YOUTUBE_COOKIES to Streamlit Secrets. Details: {last_error}"
    )


# Convert any audio/video file (.mp4 .mp3 .m4a ...) into a standard WAV file
# Standard means: 16kHz sample rate and 1 channel (mono)
# We do this even for YouTube audio, so every file has the same format
def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        output_path = os.path.splitext(input_path)[0] + "_converted.wav"
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1).set_frame_rate(16000)  # mono + 16kHz
        audio.export(output_path, format="wav")
        return output_path
    except Exception as e:
        print(f"[ERROR] Audio conversion failed for '{input_path}': {e}")
        raise


# Cut a long WAV file into small chunks (default: 10 minutes each)
# Why? A very long audio file cannot be given to Whisper in one go,
# so we cut it into small pieces and process them one by one.
def chunk_audio(wav_path: str, chunk_min: int = 10) -> list[str]:
    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    try:
        # Load the full audio file
        audio = AudioSegment.from_wav(wav_path)
        if len(audio) == 0:
            raise ValueError(f"Audio file is empty (duration 0 ms): {wav_path}")

        # pydub works in milliseconds, so convert minutes -> milliseconds
        chunk_len_ms = chunk_min * 60 * 1000

        chunks = []  # here we keep the file path of every chunk

        base_path = os.path.splitext(wav_path)[0]
        for i, start in enumerate(range(0, len(audio), chunk_len_ms)):
            chunk = audio[start: start + chunk_len_ms]   # cut one piece by slicing
            chunk_path = f"{base_path}_chunk_{i}.wav"    # name of this chunk file
            chunk.export(chunk_path, format="wav")       # save the chunk on disk

            chunks.append(chunk_path)  # remember the path

        return chunks

    except Exception as e:
        print(f"[ERROR] Failed to chunk audio file '{wav_path}': {e}")
        raise


# Main function of this file
# Takes a YouTube link or a local file and gives back a list of chunk paths
def process_input(source: str) -> list[str]:
    try:
        if source.startswith("http://") or source.startswith("https://"):
            # Input is a link -> download the audio first
            print("Detected YouTube video URL. Downloading audio...")
            raw_audio = download_youtube_audio(source)
            print("Standardizing to 16kHz mono WAV...")
            wav_path = convert_to_wav(raw_audio)
        else:
            # Input is a file on the computer
            print("Detected local file. Converting to WAV...")
            wav_path = convert_to_wav(source)

        print("Chunking audio...")
        chunks = chunk_audio(wav_path)
        print(f"Audio ready — {len(chunks)} chunk(s) created.")
        return chunks

    except Exception as e:
        print(f"[FAILURE] Audio processing aborted: {e}")
        raise RuntimeError(f"Could not download or process audio from '{source}': {e}") from e