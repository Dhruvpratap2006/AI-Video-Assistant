# here we are going to gave the summaries of all the meeting and LLM will gave one title of this meeting also

# we are going to use the mistral ai

try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

try:
    from langchain_mistralai import ChatMistralAI
except ImportError:
    ChatMistralAI = None

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

import os
from dotenv import load_dotenv
load_dotenv()

# function for calling the LLM
def get_llm():
    groq_key = os.getenv("GROQ_API_KEY")
    groq_model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip("\"'")
    if groq_model in ("llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant", "llama3-70b-8192", "llama3-8b-8192"):
        groq_model = "qwen/qwen3.8-27b"

    if ChatGroq is not None and groq_key:
        return ChatGroq(
            model=groq_model,
            groq_api_key=groq_key,
            temperature=0.3
        )
    elif ChatMistralAI is not None and os.getenv("MISTRAL_API_KEY"):
        return ChatMistralAI(
            model="open-mistral-nemo",
            mistral_api_key=os.getenv("MISTRAL_API_KEY"),
            temperature=0.3
        )
    raise ImportError("Neither GROQ_API_KEY nor MISTRAL_API_KEY is configured in your .env file.")



# function for making the chunks of the transcribed text
def split_transcript(transcript : str) -> list :
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 300,
        chunk_overlap = 200,
    )

    return splitter.split_text(transcript)


# this function will generate the summary of the meeting transcript
def get_summary(transcript : str):
    
    llm = get_llm()
    
    map_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Summarize this portion of a meeting transcript concisely."),
            ("human", "{text}"),
        ]
    )

    map_chain = map_prompt | llm | StrOutputParser()

    chunks = split_transcript(transcript) #here we are getting the chunks

    chunks_summaries = [map_chain.invoke({"text" : chunk}) for chunk in chunks] #here we are generating the summaries of the chunks

    combined = "\n\n".join(chunks_summaries)

    combined_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert meeting summarizer. Combine these partial summaries "
                "into one final professional meeting summary in bullet points.",
            ),
            ("human", "{text}"),
        ]
    )

    combined_chain = (
        RunnablePassthrough() | RunnableLambda(lambda x:{"text":x}) | combined_prompt | llm | StrOutputParser()
    )

    return combined_chain.invoke(combined)
    
    

# function for making the title 
def generate_title(transcipt : str) -> str:
    llm = get_llm()

    

    title_chain = (
        RunnablePassthrough() | RunnableLambda(lambda x:{"text":x}) | 
        ChatPromptTemplate.from_messages([
             (
                "system",
                "Based on the meeting transcript, generate a short professional meeting title "
                "(max 8 words). Only return the title, nothing else.",
            ),
            ("human", "{text}"),
        ])
        | llm
        |StrOutputParser()
    )

    return title_chain.invoke(transcipt[:2000])