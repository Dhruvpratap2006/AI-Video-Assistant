# GOAL of this file to convert the video into audio and then make chunks of that video so that we can 
# easily send this to Whisper(speech to text model) 


# we are going to use the yt-dlp to download the audio from the youtube url
# yt-dlp helps to downolad any youtube video in audio or video format

# and we are going to use the pyDub this is an python library
# which helps us to manipulate/edit the python file

# dowonolad_dir = in which all our audio , video all things be present here


from yt_dlp.utils import DownloadError
import yt_dlp
import os
import imageio_ffmpeg
from pydub import AudioSegment

DOWONOLAD_DIR = 'dowonolades'
os.makedirs(DOWONOLAD_DIR, exist_ok=True)  # this will create the dir of name downolades

# Get the path to the ffmpeg binary bundled with imageio-ffmpeg
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

# pydub needs to be told separately where ffmpeg is (yt-dlp is told below via ydl_opts)
AudioSegment.converter = FFMPEG_PATH


# this function will going to downolad the youtube_video_audio
# this code we have taken from the github of yt_dlp repo
def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWONOLAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "ffmpeg_location": FFMPEG_PATH,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "nopart": True,       # avoids Windows file-lock rename errors
        "noplaylist": True,   # download only the single video, ignore playlist/radio links
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Reliable filename derivation: strip any original extension and append .wav
            raw_filename = ydl.prepare_filename(info)
            filename = os.path.splitext(raw_filename)[0] + ".wav"

        if not os.path.exists(filename):
            raise FileNotFoundError(f"Expected audio file not found on disk: {filename}")

        return filename

    except DownloadError as e:
        print(f"[ERROR] Failed to download YouTube video: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error during download: {e}")
        raise



# this function will downolad any video which is present in .mp4 or .mp3 or in other way
# so it will downolad it in .wav file
def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    # Even though yt-dlp already gives WAV, we re-process it here to
    # standardize sample rate (16kHz) and channels (mono) for Whisper
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        output_path = os.path.splitext(input_path)[0] + "_converted.wav"
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1).set_frame_rate(16000)  # 16khz
        audio.export(output_path, format="wav")
        return output_path
    except Exception as e:
        print(f"[ERROR] Audio conversion failed for '{input_path}': {e}")
        raise




# now this function will help o make the chunk of the audio file 
# as if we have a very large audio file like 00 mins then it is not possible by 
# whispher which is speech-to-text model then it is not possible to process whole file in one go
# so we divide this into small-small segments
def chunk_audio(wav_path: str, chunk_min: int = 10) -> list[str]:
    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    try:
        # we are going to return the list as in list we will have all our chunk files
        audio = AudioSegment.from_wav(wav_path) # helps us to divide the audio file into differnt segment
        if len(audio) == 0:
            raise ValueError(f"Audio file is empty (duration 0 ms): {wav_path}")

        # we are going to have chunk min = 10 but chunking works in milliseconds 
        chunk_len_ms = chunk_min * 60 * 1000 # so here we are converting our chunks in ms

        chunks = []   # in this list we are going to store the file path of each chunk                                               
        # run a loop on this list chunks and get the each chunk one by one

        base_path = os.path.splitext(wav_path)[0]
        for i, start in enumerate(range(0, len(audio), chunk_len_ms)):
            chunk = audio[start : start + chunk_len_ms]   # this line will cut the each audio files by doing slicing
            chunk_path = f"{base_path}_chunk_{i}.wav"    # this line will save the file in the list
            chunk.export(chunk_path, format="wav")   # this line will save the file in the list

            chunks.append(chunk_path) # appending all the file paths in chunks

        return chunks

    except Exception as e:
        print(f"[ERROR] Failed to chunk audio file '{wav_path}': {e}")
        raise



# this function : it takes a video/audio source and gives you back small chunks
# which is ready for processing
def process_input(source: str) -> list[str]:
    try:
        if source.startswith("http://") or source.startswith("https://"):
            print("Detected YouTube video URL. Downloading audio...")
            raw_audio = download_youtube_audio(source)
            print("Standardizing to 16kHz mono WAV...")
            wav_path = convert_to_wav(raw_audio)
        else:
            print("Detected local file. Converting to WAV...")
            wav_path = convert_to_wav(source)

        print("Chunking audio...")
        chunks = chunk_audio(wav_path)
        print(f"Audio ready — {len(chunks)} chunk(s) created.")
        return chunks

    except Exception as e:
        print(f"[FAILURE] Audio processing aborted: {e}")
        return []



