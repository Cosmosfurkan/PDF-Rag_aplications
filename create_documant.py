from xml.dom.minidom import Document
from langchain.document_loaders.pdf import PyPDFDirectoryLoader
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from get_embedding import create_embeding_Bedrock
from langchain_community.embeddings.ollama import OllamaEmbeddings 
from langchain.vectorstores.chroma import Chroma
import argparse
import shutil


current_path = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_path, 'data')
persist_directory = os.path.join(current_path, 'db')

def load_documant():
    documant_loader = PyPDFDirectoryLoader(data_dir)
    return documant_loader.load()


def text_splitter(documant: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False
    )
    return text_splitter.split_documents(documant)


def creating_database(chunks: list[Document]):
    # Define new_chunks and new_chunks_ids

    # Use choramadb to create database
    db = Chroma(
        persist_directory=persist_directory,
        embedding_funciton=create_embeding_Bedrock()
    )
    # Calculate Page IDs.
    chunks_with_ids = calculate_chunk_ids(chunks)

    # Add or Update the documents.
    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that don't exist in the DB.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
        db.persist()
    else:
        print("✅ No new documents to add")

def calculate_chunk_ids(chunks):

    # This will create IDs like "data/monopoly.pdf:6:2"
    # Page Source : Page Number : Chunk Index

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id

    return chunks

def main():

    # Check if the database should be cleared (using the --clear flag).
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    if args.reset:
        print("✨ Clearing Database")
        clear_database()

    # Create (or update) the data store.
    documents = load_documant()
    chunks = text_splitter(documents)
    creating_database(chunks)

def clear_database():
    if os.path.exists(persist_directory):
        shutil.rmtree(persist_directory)

if __name__ == '__main__':
    main()