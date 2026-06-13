import os
import psycopg
from dotenv import load_dotenv
from google import genai
from google.genai import types
from ingestion import extract_text_from_pdf, chunk_text

load_dotenv()

ai_client = genai.Client()

def get_embedding(text: str) -> list[float]:
    """Generates a 768-dimensional vector embedding using Gemini v2."""
    response = ai_client.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
        # Force the model to safely output exactly 768 dimensions
        config=types.EmbedContentConfig(output_dimensionality=768) 
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

def run_ingestion_pipeline(pdf_path: str):
    """Coordinates the entire ingestion process from raw PDF to vector database."""
    print("Starting processing pipeline...")
    
    # 1. Extract text from the PDF
    raw_text = extract_text_from_pdf(pdf_path)
    doc_name = os.path.basename(pdf_path)
    
    # 2. Slice text into chunks
    chunks = chunk_text(raw_text, chunk_size=1000, chunk_overlap=200)
    print(f"Generated {len(chunks)} chunks. Beginning embedding process...")
    
    # 3. Process each chunk
    for i, chunk in enumerate(chunks):
        # A simple estimation of page number based on markers we inserted during extraction
        # (In a production app, you can parse this more precisely)
        page_num = i + 1 
        
        print(f"-> Processing chunk {i+1}/{len(chunks)}...")
        
        # Generate the mathematical representation
        embedding = get_embedding(chunk)
        
        # Save it to pgvector
        store_chunk_in_db(doc_name, page_num, chunk, embedding)
        
    print("\n All chunks successfully embedded and stored in PostgreSQL!")

if __name__ == "__main__":
    # Test file path
    sample_pdf = "sample.pdf"
    
    if os.path.exists(sample_pdf):
        run_ingestion_pipeline(sample_pdf)
    else:
        print(f"Please place a '{sample_pdf}' file in this directory to test the pipeline.")