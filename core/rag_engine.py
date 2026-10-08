# in this file we are going to connect our LLM with our vector store
# vector_store code is present in the file vector_store.py

import os

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
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from core.vector_store import build_vector_store, load_vector_store, get_retriever


# Function for calling the LLM via Groq API
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
    elif ChatGroq is not None:
        return ChatGroq(
            model=groq_model,
            groq_api_key=groq_key,
            temperature=0.3
        )
    raise ImportError("Neither langchain-groq nor langchain-mistralai could be initialized. Please set GROQ_API_KEY.")



def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])



def build_rag_chain(transcript:str):

    # calling the vector_store and making the retriever object
    vector_store = build_vector_store(transcript)
    retriever = get_retriever(vector_store, k = 4)

    # and now calling the llm
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(

        [(
            "system",
            """You are an expert meeting assistant. Answer the user's question 
            based ONLY on the meeting transcript context provided below.

            If the answer is not found in the context, say: 
            "I could not find this information in the meeting transcript."

            Always be concise and precise. If quoting someone, mention it clearly.

            Context from meeting transcript:
            {context}""",
        ),
        ("human", "{question}"),
        ]
    )
    

    # crerating a RAG pipeline
    rag_chain = (

        {"context" : retriever | RunnableLambda(format_docs),
         "question": RunnablePassthrough()
         }
         |prompt|llm|StrOutputParser()
    )

    return rag_chain


# LOADING THE RAG CHAIN
def load_rag_chain():
    vector_store = load_vector_store()
    retriver = get_retriever()

    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert meeting assistant. Answer the user's question 
based ONLY on the meeting transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly.

Context from meeting transcript:
{context}""",
        ),
        ("human", "{question}"),
    ])

    rag_chain = (
        {
            "context":  retriver| RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def ask_question(rag_chain, question:str) -> str:
    print(f"Question : {question}")
    answer = rag_chain.invoke(question)
    print(f"answer :{answer}")
    return answer