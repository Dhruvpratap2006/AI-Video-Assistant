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
#
# Input : list of WAV chunk paths + language (english / hinglish / hindi)
# Output: full transcript as one text string
# ---------------------------------------------------------------

import os
import requests
import whisper
from pydub import AudioSegment
from dotenv import load_dotenv

# Read the values written in the .env file
load_dotenv()

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


# Convert ONE audio chunk into text using Whisper
def transcribe_chunk_whisper(chunk_path: str) -> str:
    model = load_model()
    result = model.transcribe(chunk_path, task="transcribe")
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
    engine = "Sarvam AI" if language.lower() in ("hinglish", "hindi") else "Whisper"
    print(f"Using {engine} for transcription.")

    # Transcribe chunk by chunk and keep adding the text
    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        text = transcribe_chunk(chunk, language=language)
        full_transcript += text + " "

    print("Transcription complete.")
    return full_transcript.strip()


# Old name, kept so older code that calls transcribe_chunks still works
transcribe_chunks = transcribe_all