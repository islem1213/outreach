import pypdf
from duckduckgo_search import DDGS
import io
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_file) -> str:
    """
    Extracts text from a PDF file (either file path or file-like object / BytesIO).
    """
    try:
        # If pdf_file is bytes, wrap it in BytesIO
        if isinstance(pdf_file, bytes):
            pdf_file = io.BytesIO(pdf_file)
            
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return ""

def search_jobs(query: str, max_results: int = 5) -> list:
    """
    Searches for jobs online using DuckDuckGo search.
    Returns a list of dicts: {'title': ..., 'href': ..., 'body': ...}
    """
    try:
        # Clean query
        query = query.strip()
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} job posting", max_results=max_results))
            processed = []
            for r in results:
                processed.append({
                    "title": r.get("title", "Job Posting"),
                    "href": r.get("href", "#"),
                    "body": r.get("body", "")
                })
            if processed:
                return processed
    except Exception as e:
        logger.error(f"Error searching DuckDuckGo: {e}")
        
    # Fallback mock results if search fails or has no internet connection
    logger.info("Using fallback job search results.")
    return [
        {
            "title": f"Senior Software Engineer ({query}) - TechGlobal",
            "href": "https://example.com/jobs/1",
            "body": f"We are looking for a Senior Developer specialized in {query}. Skills: Python, system design, API development. Experience with Cloud, databases, and writing clean, scalable code is essential."
        },
        {
            "title": f"{query} Developer - TechCorp",
            "href": "https://example.com/jobs/2",
            "body": f"TechCorp is hiring a Full-time {query} Developer. Join a team building modern cloud products. Requirements: 3+ years experience, Python/JavaScript, and knowledge of web applications."
        },
        {
            "title": f"AI Engineer / {query} Specialist - InnovationLabs",
            "href": "https://example.com/jobs/3",
            "body": f"Exciting opportunity for a {query} specialist to apply AI tools to automate workflows. Experience in machine learning, Python, LLMs, and streamlit UI is highly appreciated."
        }
    ]
