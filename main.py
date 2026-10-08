# here we are going to connect all the functionalities

# writing the code for terminal output

from dotenv import load_dotenv
from utils.audio_process import process_input
from core.transcribers import transcribe_all
from core.summarize import get_summary, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()



# function for running the entire process
def run_pipeline(source : str, language : str = "english")  -> dict :
    # basically here the source is str can be a youtube link or a local path of any video
    # language is the language of the video content and that can be both english or hindi 
    # but if user do not gave any language then by default it will be english

    print("starting AI Video Assistant") 

    chunks = process_input(source)
    transcript = transcribe_all(chunks, language)
    print(f"raw transcription (first 300 characters ) {transcript[:300]}")

    title = generate_title(transcript)
    print(f"generated title: {title}")

    summary = get_summary(transcript)

    action_item = extract_action_items(transcript)

    decisions = extract_key_decisions(transcript)
    questions = extract_questions(transcript)
    
    rag_chain = build_rag_chain(transcript)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_item,
        "decisions": decisions,
        "questions": questions,
        "rag_chain": rag_chain,
    }


if __name__ == "__main__":
        source = input("Enter YouTube URL or local file path: ").strip()
        language = input("Language (english/hinglish): ").strip() or "english"
        result = run_pipeline(source, language)

        print("\n" + "=" * 60)
        print(f"📌 Title: {result['title']}")
        print(f"\n📋 Summary:\n{result['summary']}")
        print(f"\n✅ Action Items:\n{result['action_items']}")
        print(f"\n🔑 Key Decisions:\n{result['decisions']}")
        print(f"\n❓ Open Questions:\n{result['questions']}")
        print("=" * 60)

        print("\n💬 Chat with your meeting (type 'exit' to quit)\n")
        rag_chain = result["rag_chain"]
        while True:
            question = input("You: ").strip()
            if question.lower() in ["exit", "quit", "q"]:
                print("👋 Goodbye!")
                break
            if not question:
                continue
            answer = ask_question(rag_chain, question)
            print(f"\n🤖 Assistant: {answer}\n")