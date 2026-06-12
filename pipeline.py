import os
import psycopg
from dotenv import load_dotenv
from google import genai
from ingestion import extract_text_from_pdf, chunk_text

load_dotenv()

ai_client = genai.Client()

def get_embedding(text: str) -> list[float]:
    """Generates a 768-dimensional vector embedding using Gemini."""
    response = ai_client.models.embed_content(
        model="text-embedding-004",
        contents=text
    )
    return response.embeddings[0].values

def store_chunk_in_db(doc_name: str, page_num: int, content: str, embedding: list[float]):
    """Connects to PostgreSQL and inserts a single document chunk."""
    conn_string = f"host={os.getenv('DB_HOST')} port={os.getenv('DB_PORT')} dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')}"
    
    # Open connection and cursor safely
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO document_chunks (document_name, page_number, chunk_content, embedding)
                VALUES (%s, %s, %s, %s);
                """,
                (doc_name, page_num, content, embedding)
            )
        # Commit changes to the database
        conn.commit()