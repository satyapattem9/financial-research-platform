import os
import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Financial Research Platform API")
ai_client = genai.Client()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your React dev server (port 5173) to connect
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

def get_query_embedding(text: str) -> list[float]:
    """Converts the user's question into the 768-dimensional vector space."""
    response = ai_client.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    return response.embeddings[0].values

def semantic_search(query_vector: list[float], limit: int = 4) -> list[dict]:
    """Queries pgvector using cosine distance to find the closest context chunks."""
    conn_string = f"host={os.getenv('DB_HOST')} port={os.getenv('DB_PORT')} dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')}"
    results = []
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT document_name, page_number, chunk_content 
                FROM document_chunks 
                ORDER BY embedding <=> %s::vector 
                LIMIT %s;
                """,
                (query_vector, limit)
            )
            rows = cur.fetchall()
            for row in rows:
                results.append({
                    "document": row[0],
                    "page": row[1],
                    "content": row[2]
                })
    return results

@app.post("/query")
def ask_question(request: QueryRequest):
    """
    RAG Endpoint: Retrieves relevant context from pgvector, synthesizes 
    a grounded response using Gemini, and returns the result with citations.
    """
    try:
        # 1. Vectorize user question
        query_vector = get_query_embedding(request.question)
        
        # 2. Pull matching text chunks from the database
        matched_chunks = semantic_search(query_vector)
        
        if not matched_chunks:
            return {"answer": "No relevant data found in the knowledge base.", "sources": []}
            
        # 3. Format the text blocks into a structured context window for the LLM
        context_str = ""
        sources_list = []
        for i, chunk in enumerate(matched_chunks):
            source_identifier = f"Source {i+1} [Doc: {chunk['document']}, Page: {chunk['page']}]"
            context_str += f"\n--- {source_identifier} ---\n{chunk['content']}\n"
            sources_list.append({
                "label": f"Source {i+1}",
                "document": chunk["document"],
                "page": chunk["page"]
            })
            
        # 4. Craft a strict system prompt to completely block hallucinations
        system_prompt = (
            "You are an expert financial analyst. Answer the user's question using ONLY the provided text segments. "
            "For every key claim or metric you provide, you MUST explicitly cite which source it came from (e.g., [Source 1]). "
            "If the provided text does not contain the answer, state that you cannot find the information in the documents."
        )
        
        user_prompt = f"Contextual Data:\n{context_str}\n\nQuestion: {request.question}"
        
        # 5. Synthesize the grounded response using Gemini
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",  # Using the flagship fast text generation model
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2  # Keep temperature low for deterministic, factual extraction
            )
        )
        
        return {
            "status": "success",
            "answer": response.text,
            "sources_used": sources_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))