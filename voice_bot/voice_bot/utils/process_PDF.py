import hashlib
import os

import fitz
import numpy as np
import pymongo
from google import genai
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from sklearn.metrics.pairwise import cosine_similarity

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["data"]
collection_pdf = db["pdf"]
collection_embedding = db["embedding"]
collection_pdf_user = db["pdf_user"]
collection_embedding_user = db["embedding_user"]


def generate_hash(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def read_pdf(pdf_path):
    documents = []
    with fitz.open(pdf_path) as pdf:
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            text = page.get_text()  # Trích xuất văn bản từ trang
            documents.append(text)
    return "\n".join(documents)


def save_pdf_to_mongodb(folder_path):
    pdf_files = [pdf for pdf in os.listdir(folder_path) if pdf.endswith((".pdf", ".txt"))]

    for pdf_file in pdf_files:
        file_path = os.path.join(folder_path, pdf_file)
        # Trích xuất nội dung PDF
        pdf_content = read_pdf(file_path)
        if pdf_content:
            pdf_hash = generate_hash(pdf_content)
            if collection_pdf.find_one({"hash": pdf_hash}):
                print(f"Duplicate detected: {pdf_file} already exists in MongoDB. Skipping...")
                continue
            pdf_data = {
                "name": pdf_file,
                "content": pdf_content,
                "hash": pdf_hash,
            }
            collection_pdf.insert_one(pdf_data)
            print(f"Saved {pdf_file} to MongoDB.")
    print("All PDFs have been saved to MongoDB.")


def save_pdf_user_to_mongodb(file_input):
    pdf_content_user = read_pdf(file_input)
    if pdf_content_user:
        pdf_hash = generate_hash(pdf_content_user)
        if collection_pdf_user.find_one({"hash": pdf_hash}):
            print(f"Duplicate detected: {file_input} already exists in MongoDB. Skipping...")
        else:
            pdf_data = {
                "name": file_input,
                "content": pdf_content_user,
                "hash": pdf_hash,
            }
            collection_pdf_user.insert_one(pdf_data)
            print(f"Saved {file_input} to MongoDB.")


def process_pdf(docs, chunk_size=1000, chunk_overlap=200):
    """Split documents into chunks and generate embeddings."""
    if isinstance(docs, str):
        docs = [docs]
    print("process_documents")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = text_splitter.create_documents(docs)
    # Remove empty chunks
    chunks = [chunk for chunk in chunks if chunk.page_content.strip()]
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return chunks, embeddings


def build_vector_store(chunks, embeddings): 
    print("Building vector store...")
    try:
        for chunk in chunks:
            chunk_hash = generate_hash(chunk.page_content)
            existing_document = collection_embedding.find_one({"chunk_hash": chunk_hash})

            if existing_document:
                print(f"Chunk already exists: {chunk_hash}. Skipping...")
                continue

            # Đảm bảo tính toán embedding và chuyển thành định dạng có thể serial hóa (chuyển thành danh sách nếu cần)
            embedding = embeddings.embed_query(chunk.page_content)
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()  # Chuyển NumPy array thành danh sách
            
            document = {
                "chunk_hash": chunk_hash,
                "content": chunk.page_content,
                "embedding": embedding,  # Bây giờ là dạng danh sách có thể serial hóa
            }

            collection_embedding.insert_one(document)

        print(f"Vector store built successfully for collection: {collection_embedding}")
    except Exception as e:
        print(f"Error in building vector store: {e}")
        raise e

def build_vector_store_user(chunks, embeddings):
    print("Building vector store...")
    try:
        for chunk in chunks:
            # Generate a unique hash for the chunk
            chunk_hash = generate_hash(chunk.page_content)
            existing_document = collection_embedding_user.find_one({"chunk_hash": chunk_hash})

            if existing_document:
                print(f"Chunk already exists: {chunk_hash}. Skipping...")
                continue
            
            # Generate embedding vector for the chunk content
            embedding_vector = embeddings.embed_query(chunk.page_content)
            
            # Prepare the document for MongoDB
            document = {
                "chunk_hash": chunk_hash,
                "content": chunk.page_content,
                "embedding": embedding_vector,  # Ensure it's a list of floats
            }

            # Insert the document into the MongoDB collection
            collection_embedding_user.insert_one(document)

        print(f"Vector store built successfully for collection: {collection_embedding_user}")
    except Exception as e:
        print(f"Error in building vector store: {e}")
        raise e

   

def load_vector_store():
        try:
            all_documents = collection_embedding.find()
            vector_store = [
                {"chunk_hash": doc["chunk_hash"], "content": doc["content"], "embedding": doc["embedding"]}
                for doc in all_documents
            ]

            print(f"Loaded {len(vector_store)} documents from vector store.")
            return vector_store
        except Exception as e:
            print(f"Error loading vector store: {e}")
            return []

def load_vector_store_user():
        try:
            all_documents = collection_embedding_user.find()
            vector_store = [
                {"chunk_hash": doc["chunk_hash"], "content": doc["content"], "embedding": doc["embedding"]}
                for doc in all_documents
            ]

            print(f"Loaded {len(vector_store)} documents from vector store.")
            return vector_store
        except Exception as e:
            print(f"Error loading vector store: {e}")
            return []



def build_chain(vector_store, vector_store_user, user_input, embeddings):
        print("Building chain...")
    
        # Compute embedding vector for the user query
        user_embedding = np.array(embeddings.embed_query(user_input))
        
        # Find the nearest documents using cosine similarity
        similarities = []
        for doc in vector_store:
            doc_embedding = np.array(doc["embedding"])
            similarity = cosine_similarity(
                user_embedding.reshape(1, -1),
                doc_embedding.reshape(1, -1),
            )[0][0]
            similarities.append((similarity, doc))
        context = ""
        # If no similar documents found, check the user vector store
        if not similarities:
            context += "No relevant information found from the user-provided document."
            for doc in vector_store_user:
                context += "Relevant information found in the knowledge base: "
                doc_embedding = np.array(doc["embedding"])
                similarity = cosine_similarity(
                    user_embedding.reshape(1, -1),
                    doc_embedding.reshape(1, -1),
                )[0][0]
                similarities.append((similarity, doc))
            if not similarities:
                context += "No relevant information found in the knowledge base."
            else:
                top_docs = sorted(similarities, key=lambda x: x[0], reverse=True)[:3]
                context += " ".join([doc["content"] for _, doc in top_docs])
        else:
            context += "relevant information found from the user-provided document: "
            top_docs = sorted(similarities, key=lambda x: x[0], reverse=True)[:3]
            context += " ".join([doc["content"] for _, doc in top_docs])

        print("Context:")
        print(context)
        print("Query:")
        print(user_input)
        text = f"""
        You will answer the user's question based on the following information:
        {context}.

        If no relevant information is found, you should:
        - Inform the user that no information was found.

        Question: {user_input}

        Answer:
        """


        os.environ["GOOGLE_API_KEY"] = "AIzaSyDDor0KKmMki-YYMXQ-kMizGTbhWM1rmwk"
        api_key = os.getenv("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.0-flash-exp", contents=text)
        return response.text



def get_chain(user_input, folder_path, file_input):
    """Build or load vector store and chain."""
    print("Building the index from documents...")
    save_pdf_to_mongodb(folder_path)
    save_pdf_user_to_mongodb(file_input)

    all_docs = [doc["content"] for doc in collection_pdf.find()]
    docs_user = [doc["content"] for doc in collection_pdf_user.find()]

    chunks, embeddings = process_pdf(all_docs)
    chunks_user, embeddings_user = process_pdf(docs_user)
    build_vector_store(chunks, embeddings)
    build_vector_store_user(chunks_user, embeddings_user)
    print("Done build_vector_store")

    vector_store = load_vector_store()
    vector_store_user = load_vector_store_user()
    response = build_chain(vector_store, vector_store_user, user_input, embeddings)
    print("Response from LLM:")
    print(response)
    return response


# collection_embedding.delete_many({})
'''
if __name__ == "__main__":
    folder_path = "C:/Users/Asus/Desktop/Job/hekate/void_bot/void_bot/PDF_data"
    file_input = "C:/Users/Asus/Desktop/Job/hekate/void_bot/void_bot/PDF_data/bert.pdf"
    user_query = "Explain the key points of the documents related to AI research."
    get_chain(user_query, folder_path, file_input)
'''
