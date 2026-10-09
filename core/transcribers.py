# ---------------------------------------------------------------
#               AI Transcription
# File    : core/transcribers.py
# Purpose : Convert audio chunks into text
#           - English audio  -> Whisper (runs on your own computer)
#           - Hindi/Hinglish -> Sarvam AI (online API, gives English text)
# ---------------------------------------------------------------
#
# What this file does:
# 1. Loads the Whisper model only once (so it is not loaded again and again)
# 2. Converts each audio chunk into text, one by one
# 3. For Hindi/Hinglish, sends audio to Sarvam AI which returns English text
# 4. Joins the text of all chunks into one full transcript
# 5. Whisper model size (tiny / small / medium / large) is set in the .env file
# 6. NEW: can also give the time (start and end) of every piece of text,
#    so later we can say "this answer is from 12:40 in the video"
#
# Input : list of WAV chunk paths + language (english / hinglish / hindi)
# Output: 
#   transcribe_all()                -> full transcript as one text string
#   transcribe_all_with_segments()  -> dictionary with full text + timed segments
# ---------------------------------------------------------------

import os
import wave
import requests
import whisper
from pydub import AudioSegment
from dotenv import load_dotenv

# Read the values written in the .env file
load_dotenv()

# Groq API configuration for ultra-fast cloud Whisper transcription
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip("\"'")
groq_client = None
if GROQ_API_KEY:
    try:
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Notice: Groq client could not be initialized ({e}). Using local Whisper.")
        groq_client = None

# Sarvam does not accept audio longer than 30 seconds.
# So we cut audio into 25 second pieces (5 seconds kept as safety gap).
SARVAM_PIECE_SECONDS = 25

# Which Whisper model to use. If nothing is set in .env, use "small".
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

# Sarvam API key from .env (strip removes extra quote marks if any)
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip("\"'")

# Sarvam API link for speech-to-text + translate to English
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"

# Sarvam model name
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5").strip("\"'")

# Whisper model is not loaded yet, so it starts as None
_model = None


# Load the Whisper model (only the first time, after that reuse it)
def load_model():
    global _model

    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL} ...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("Whisper model loaded.")
    return _model


# ---------------------------------------------------------------
# PART 1 : TEXT ONLY (this is the old code, it works as before)
# ---------------------------------------------------------------

# Convert ONE audio chunk into text using Whisper (Groq fast API with local Whisper fallback)
def transcribe_chunk_whisper(chunk_path: str) -> str:
    if groq_client:
        try:
            with open(chunk_path, "rb") as audio_file:
                transcription = groq_client.audio.transcriptions.create(
                    file=(os.path.basename(chunk_path), audio_file),
                    model="whisper-large-v3-turbo",
                    response_format="json",
                )
            return transcription.text
        except Exception as e:
            print(f"Groq Whisper error ({e}), falling back to local Whisper...")

    model = load_model()
    result = model.transcribe(chunk_path, task="transcribe", fp16=False)
    return result["text"]


# Send ONE small WAV file (max 30s) to Sarvam and get English text back
def _send_to_sarvam(piece_path: str) -> str:
    # Get the API key and put it in the request header
    api_key = (SARVAM_API_KEY or os.getenv("SARVAM_API_KEY", "")).strip("\"'")
    headers = {"api-subscription-key": api_key}

    # Open the audio file and send it to Sarvam
    with open(piece_path, "rb") as f:
        files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
        data = {"model": SARVAM_MODEL, "with_diarization": "false"}
        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    # If Sarvam gave an error, print it so we can see what went wrong
    if not response.ok:
        print(f"\n❌ Sarvam returned {response.status_code}")
        print(f"Response body: {response.text}\n")
        response.raise_for_status()

    # Take out the text from the response
    return response.json().get("transcript", "")


# Convert ONE audio chunk into English text using Sarvam
# Sarvam takes only 30s audio, so we cut the chunk into 25s pieces first
def transcribe_chunk_sarvam(chunk_path: str) -> str:
    api_key = (SARVAM_API_KEY or os.getenv("SARVAM_API_KEY", "")).strip("\"'")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    # Load the chunk and find the piece length in milliseconds
    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    full_text = ""
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms  # round up

    # Go through the chunk piece by piece
    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start: start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")  # save the piece as a temp file

        try:
            print(f"  → Sarvam piece {i + 1}/{total_pieces} ...")
            full_text += _send_to_sarvam(piece_path) + " "
        finally:
            # Delete the temp file, even if an error happened
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return full_text.strip()


# Pick the right tool for ONE chunk based on language
#   english            -> Whisper
#   hinglish / hindi   -> Sarvam
def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    if language.lower() in ("hinglish", "hindi"):
        return transcribe_chunk_sarvam(chunk_path)
    return transcribe_chunk_whisper(chunk_path)


# Convert ALL chunks into text and join them into one transcript
def transcribe_all(chunks: list, language: str = "english") -> str:
    full_transcript = ""

    # Just for printing which engine is being used
    if language.lower() in ("hinglish", "hindi"):
        engine = "Sarvam AI"
    elif groq_client:
        engine = "Groq Whisper (whisper-large-v3-turbo - Ultra Fast)"
    else:
        engine = f"Local Whisper ({WHISPER_MODEL})"
    print(f"Using {engine} for transcription.")

    # Transcribe chunk by chunk and keep adding the text
    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        text = transcribe_chunk(chunk, language=language)
        full_transcript += text + " "

    print("Transcription complete.")
    return full_transcript.strip()


# ---------------------------------------------------------------
# PART 2 : TEXT + TIME (this is the new code)
# A "segment" is one small piece of text with its start and end time:
#   {"text": "Hello everyone", "start": 12.5, "end": 15.0}
# ---------------------------------------------------------------

# Find the real length of a WAV chunk in seconds
# We need this to know where the next chunk starts in the full video
def _chunk_length_seconds(chunk_path: str) -> float:
    with wave.open(chunk_path, "rb") as wav_file:
        # length in seconds = total frames / frames per second
        return wav_file.getnframes() / wav_file.getframerate()


# Convert ONE chunk using Whisper and keep the time of every sentence
# Important: these times start from 0 at the start of THIS chunk only
def transcribe_chunk_whisper_segments(chunk_path: str) -> list:
    if groq_client:
        try:
            with open(chunk_path, "rb") as audio_file:
                transcription = groq_client.audio.transcriptions.create(
                    file=(os.path.basename(chunk_path), audio_file),
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json",
                )

            segments = []
            for seg in getattr(transcription, "segments", []):
                text = seg.get("text", "").strip() if isinstance(seg, dict) else seg.text.strip()
                start = seg.get("start", 0.0) if isinstance(seg, dict) else seg.start
                end = seg.get("end", 0.0) if isinstance(seg, dict) else seg.end
                if text:
                    segments.append({"text": text, "start": start, "end": end})
            return segments
        except Exception as e:
            print(f"Groq Whisper error ({e}), falling back to local Whisper...")

    model = load_model()
    result = model.transcribe(chunk_path, task="transcribe", fp16=False)

    segments = []
    for seg in result["segments"]:
        text = seg["text"].strip()
        # skip empty pieces
        if text:
            segments.append({"text": text, "start": seg["start"], "end": seg["end"]})
    return segments


# Convert ONE chunk using Sarvam and keep the time of every 25s piece
# Sarvam does not give sentence times, so each 25s piece becomes one segment
# Important: these times also start from 0 at the start of THIS chunk only
def transcribe_chunk_sarvam_segments(chunk_path: str) -> list:
    api_key = (SARVAM_API_KEY or os.getenv("SARVAM_API_KEY", "")).strip("\"'")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms  # round up

    segments = []
    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start: start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")  # save the piece as a temp file

        try:
            print(f"  → Sarvam piece {i + 1}/{total_pieces} ...")
            text = _send_to_sarvam(piece_path).strip()
        finally:
            # Delete the temp file, even if an error happened
            if os.path.exists(piece_path):
                os.remove(piece_path)

        if text:
            segments.append({
                "text": text,
                "start": start / 1000,                        # ms -> seconds
                "end": min(start + piece_ms, len(audio)) / 1000,
            })
    return segments


# Convert ALL chunks and return the full text AND the segments
# with the REAL time of the full video
#
# Why "offset"?
# Every chunk starts counting time from 0. But chunk 2 really starts at 10:00
# in the video. So after each chunk we add its length to "offset", and we add
# this offset to every segment time of the next chunk.
def transcribe_all_with_segments(chunks: list, language: str = "english") -> dict:
    is_indian = language.lower() in ("hinglish", "hindi")

    # Just for printing which engine is being used
    if is_indian:
        engine = "Sarvam AI"
    elif groq_client:
        engine = "Groq Whisper (whisper-large-v3-turbo - Ultra Fast)"
    else:
        engine = f"Local Whisper ({WHISPER_MODEL})"
    print(f"Using {engine} for transcription.")

    all_segments = []
    offset = 0.0  # seconds of the video that are already finished

    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")

        # Pick the right tool for this language
        if is_indian:
            chunk_segments = transcribe_chunk_sarvam_segments(chunk)
        else:
            chunk_segments = transcribe_chunk_whisper_segments(chunk)

        # Move chunk times to the real video time by adding the offset
        for seg in chunk_segments:
            all_segments.append({
                "text": seg["text"],
                "start": round(seg["start"] + offset, 2),
                "end": round(seg["end"] + offset, 2),
            })

        # The next chunk starts where this one ended
        offset += _chunk_length_seconds(chunk)

    # Join all the text into one full transcript
    full_text = " ".join(seg["text"] for seg in all_segments)

    print("Transcription complete.")
    return {"text": full_text, "segments": all_segments}


# Old name, kept so older code that calls transcribe_chunks still works
transcribe_chunks = transcribe_all