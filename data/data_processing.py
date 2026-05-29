import csv 
import json
import os
from dotenv import load_dotenv

from openai import OpenAI
import psycopg

load_dotenv()

csv_file_path = "data/rag_sample_data.csv"

def connect_db():
    return psycopg.connect(
        host=os.getenv("DATABASE_HOST"),
        port=os.getenv("DATABASE_PORT", 5432),
        dbname=os.getenv("DATABASE_NAME", "postgres"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD")
    )

def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS FQA_embedding (
            id SERIAL PRIMARY KEY,
            chunk_id INT,
            text_content TEXT NOT NULL,
            metadata JSONB,
            embedding VECTOR(1536) 
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

def create_chunks(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def generate_embedding(text):
    client = OpenAI(api_key=os.getenv("OPENAI_API_EMBEDDING_KEY"),
                     base_url="https://models.inference.ai.azure.com")
    
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small" 
    )
    vector = response.data[0].embedding
    return vector

def insert_embedding(chunk_id, text_content, metadata, embedding):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO FQA_embedding (chunk_id, text_content, metadata, embedding)
        VALUES (%s, %s, %s, %s);
    """, (chunk_id, text_content, json.dumps(metadata), embedding))
    conn.commit()
    cursor.close()
    conn.close()

def process_csv_and_store_embeddings(file_path):
    create_table()
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)    
        for row in reader:
            text = row['text']
            metadata = {
                "topic": row['topic'],
                "sample_question": row['sample_question'],
                "sample_ground_truth": row['sample_ground_truth']
            }
            chunks = create_chunks(text)
            for idx, chunk in enumerate(chunks):
                embedding = generate_embedding(chunk)
                insert_embedding(idx, chunk, metadata, embedding)

if __name__ == "__main__":
    process_csv_and_store_embeddings("data/rag_sample_data.csv") 
    print("Data processing and embedding storage completed successfully.")               