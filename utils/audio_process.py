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

from yt_dlp.utils import DownloadError
import yt_dlp
import os
import imageio_ffmpeg
from pydub import AudioSegment

# Folder where all downloaded audio and chunks are saved
DOWONOLAD_DIR = 'dowonolades'
os.makedirs(DOWONOLAD_DIR, exist_ok=True)  # create the folder if it is not there

# Get the path of the ffmpeg tool that comes with imageio-ffmpeg
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

# pydub also needs to know where ffmpeg is
# (yt-dlp gets this path separately, inside ydl_opts below)
AudioSegment.converter = FFMPEG_PATH


# Download the audio of a YouTube video and save it as a WAV file
def download_youtube_audio(url: str) -> str:
    """Download audio from YouTube using robust client emulation to bypass HTTP 403 bot blocks."""
    output_template = os.path.join(DOWONOLAD_DIR, "%(id)s.%(ext)s")

    client_strategies = [
        ["ios", "android", "mweb"],
        ["android", "web"],
        ["mweb", "ios"],
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
        f"YouTube frequently restricts automated stream access. "
        f"Please try a different YouTube link, or use the 'Upload File' tab to upload the recording (.mp4, .mp3, .wav) directly. "
        f"Details: {last_error}"
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