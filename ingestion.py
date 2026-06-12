import os
import pymupdf

def extract_text_from_pdf(pdf_path: str) -> str:
    """Opens a PDF file and extracts all text content page by page."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Could not find the file at: {pdf_path}")
        
    full_text = ""
    with pymupdf.open(pdf_path) as doc:
        print(f"--- Processing: {pdf_path} ({len(doc)} pages) ---")
        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            if page_text.strip():
                full_text += f"\n--- PAGE {page_num + 1} ---\n"
                full_text += page_text
    return full_text

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """
    Splits a long string of text into smaller segments using a sliding window.
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    # loops through the text moving the window forward by (chunk_size - chunk_overlap)
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        
        # moves the starting point forward, but step back by the overlap amount
        start += (chunk_size - chunk_overlap)
        
    return chunks

if __name__ == "__main__":
    sample_pdf = "sample.pdf"
    
    try:
        # 1. extract text
        raw_text = extract_text_from_pdf(sample_pdf)
        
        # 2. chunk text
        document_chunks = chunk_text(raw_text, chunk_size=1000, chunk_overlap=200)
        
        print(f"\nProcessing Complete!")
        print(f"Total characters extracted: {len(raw_text)}")
        print(f"Total chunks generated: {len(document_chunks)}")
        
        # 3. print a couple of sample chunks to verify the overlap
        if len(document_chunks) > 1:
            print("\n--- SAMPLE CHUNK 1 ---")
            print(document_chunks[0][:300] + "... [TRUNCATED]")
            print("\n--- SAMPLE CHUNK 2 ---")
            print(document_chunks[1][:300] + "... [TRUNCATED]")

    except FileNotFoundError as e:
        print(f"Setup Notice: {e}")
        print("Tip: Drop a sample financial PDF into this folder and rename it to 'sample.pdf' to test!")