"""Helper utilities for the Deep Research Assistant."""

import re
from typing import List, Dict, Any

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into chunks with overlap."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def format_evidence(evidence: Dict[str, Any]) -> str:
    """Format evidence for display."""
    return f"Title: {evidence.get('title', 'Unknown')}\nContent: {evidence.get('content', '')}"


