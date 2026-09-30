# here we are going to gave the summaries of all the meeting and LLM will gave one title of this meeting also

# we are going to use the mistral ai

from whisper import model
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

import os
from dotenv import load_dotenv
load_dotenv()

# function for calling the LLM
def get_llm():
    return ChatMistralAI(model="open-mistral-nemo", mistral_api_key=os.getenv("MISTRAL_API_KEY"), temperature=0.3)



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

    chunks_summaries = [map.chain.invoke({"text" : chunk}) for chunk in chunks] #here we are generating the summaries of the chunks

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