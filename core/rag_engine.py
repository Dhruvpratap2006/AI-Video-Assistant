# in this file we are going to connect our LLM with our vector store
# vector_store code is present in the file vector_store.py

import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from core.vector_store import build_vector_store, load_vector_store, get_retriever


# function for calling the llm
def get_llm():
    return ChatMistralAI(
        model="open-mistral-nemo",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3,
    )


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