# code for testing sarvam

# from dotenv import load_dotenv
# load_dotenv()
# from utils.audio_process import process_input
# from core.transcribers import transcribe_all
# import os


# print("KEY LOADED:", os.getenv("SARVAM_API_KEY"))   # should print your key
# print("CWD:", os.getcwd())

# source = "https://www.youtube.com/watch?v=tplWXd_T7YQ"
# language = "hinglish"   # change to "hinglish" to test Sarvam

# chunks = process_input(source)
# transcript = transcribe_all(chunks, language=language)

# print("\n=== TRANSCRIPT ===\n")
# print(transcript)


# code for testing whisper
from dotenv import load_dotenv
load_dotenv()
from utils.audio_process import process_input
from core.transcribers import transcribe_all
import os

print("CWD:", os.getcwd())

source = "http://youtube.com/watch?v=itWkn_N_XjM&list=RDitWkn_N_XjM&start_radio=1"
language = "english"   # english = Whisper, hinglish/hindi = Sarvam

chunks = process_input(source)
transcript = transcribe_all(chunks, language=language)

print("\n=== TRANSCRIPT ===\n")
print(transcript)


