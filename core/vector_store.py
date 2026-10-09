import os  

from langchain_community.vectorstores import Chroma

# HuggingFaceEmbeddings = loads a free model that converts text into numbers
from langchain_community.embeddings import HuggingFaceEmbeddings

# RecursiveCharacterTextSplitter = cuts a big text into small pieces (chunks)
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Document = a small box that holds one chunk of text + extra info about it
from langchain_core.documents import Document


# ---------------------------------------------------------------
# SETTINGS (change them here, they are used everywhere below)
# ---------------------------------------------------------------

# Folder name on your computer where the database will be saved.
# Because it is saved on disk, data stays even after you close the program.
CHROMA_DIR = "vector_db"

# Name of the "table" inside the database where chunks are stored.
COLLECTION_NAME = "meeting_transcript"

# The model that converts text into numbers.
# "all-MiniLM-L6-v2" is small, fast, and free.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# ---------------------------------------------------------------
# FUNCTION 1: load the embedding model
# ---------------------------------------------------------------
def get_embeddings():
    # An embedding = a list of numbers that represents the MEANING of a text.
    # Texts with similar meaning get similar numbers.
    # This is how we can search by meaning and not only by exact words.
    return HuggingFaceEmbeddings(
        model_name = EMBEDDING_MODEL,        # which model to use
        model_kwargs = {"device" : 'cpu'}    # run it on CPU (no GPU needed)
    )


# ---------------------------------------------------------------
# FUNCTION 2: build the database from a transcript (run this FIRST TIME)
# ---------------------------------------------------------------
def build_vector_store(transcript : str)->Chroma:
    # Just a message so you know that this function has started
    print("Building vector Store")

    # Step 1: make the splitter (the tool that cuts text)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,     # each chunk will be around 500 characters long
        chunk_overlap = 50    # each chunk repeats the last 50 characters of the
                              # previous chunk, so a sentence cut in the middle
                              # does not lose its meaning
    )

    # Step 2: cut the full transcript into a list of small text pieces
    chunks = splitter.split_text(transcript)

    # Step 3: put every chunk into a Document box.
    # metadata = extra info. Here we save the chunk number (0, 1, 2, ...)
    # so later we know which part of the transcript a chunk came from.
    docs = [
        Document(page_content=chunk, metadata = {'chunk_index' : i})
        for i,chunk in enumerate(chunks)
    ]

    # Step 4: load the embedding model (text -> numbers converter)
    embeddings = get_embeddings()

    # Step 5: convert every chunk into numbers and save everything in Chroma.
    vector_store = Chroma.from_documents(
        documents= docs,                    # the chunks we made above
        embedding=embeddings,               # the model that makes the numbers
        collection_name=COLLECTION_NAME,    # table name inside the database
        persist_directory=CHROMA_DIR        # folder where it is saved on disk
    )

    # Give the database back so other files can use it
    return vector_store


# ---------------------------------------------------------------
# FUNCTION 3: open an already-built database (use this from the 2nd time)
# ---------------------------------------------------------------
def load_vector_store() ->Chroma:
    # We need the SAME embedding model that was used while building.
    # Reason: the user's question must be converted to numbers in the same
    # way as the saved chunks, otherwise comparing them makes no sense.
    embeddings = get_embeddings()

    # Open the existing database from the folder (nothing is rebuilt here)
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,      # same table name as before
        embedding_function= embeddings,       # used to convert new questions
        persist_directory=CHROMA_DIR          # folder where data was saved
    )

    return vector_store


# ---------------------------------------------------------------
# FUNCTION 4: make a retriever (the "search" tool)
# ---------------------------------------------------------------
# THIS FUNCTION will help us to retrieve only the top k elements
def get_retriever(vector_store : Chroma, k :int = 4):
    # A retriever takes a question, converts it to numbers, compares it with
    # all saved chunks, and returns the closest ones.
    return vector_store.as_retriever(
        search_type = 'similarity',   # find chunks whose meaning is most similar
        search_kwargs = {"k":k}       # k = how many chunks to return (default 4)
    )


# ---------------------------------------------------------------
# HOW TO USE THIS FILE (example, from another file)
# ---------------------------------------------------------------
# First time (new transcript):
#     vs = build_vector_store(transcript_text)
#
# Next times (database already exists):
#     vs = load_vector_store()
#
# Then search:
#     retriever = get_retriever(vs)
#     results = retriever.invoke("What was decided about the deadline?")
#     for r in results:
#         print(r.page_content)