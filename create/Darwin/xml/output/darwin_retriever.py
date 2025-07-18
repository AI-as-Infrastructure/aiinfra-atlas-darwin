#!/usr/bin/env python3
"""
Auto-generated ATLAS Retriever for Darwin Corpus
Generated: 2025-07-17 12:12:17
Manifest creation: 2025-07-17 11:58:55
"""
import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents.base import Document
from backend.retrievers.base_retriever import BaseRetriever

logger = logging.getLogger(__name__)

# Define direction filter options
DIRECTION_OPTIONS = [
    {"value": "all", "label": "All Letters"},
    {"value": "sent", "label": "Sent by Darwin"},
    {"value": "received", "label": "Received by Darwin"}
]

# Define time period options
TIME_PERIOD_OPTIONS = [
    {"value": "all", "label": "All Years"},
    {"value": "1821-1840", "label": "Early Years (1821-1840)"},
    {"value": "1831-1850", "label": "Voyage & Development (1831-1850)"},
    {"value": "1850-1870", "label": "Origin Period (1850-1870)"},
    {"value": "1870-1882", "label": "Later Years (1870-1882)"}
]


class DarwinRetriever(BaseRetriever):
    """Darwin corpus retriever implementation for ATLAS."""
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
        
        config["DIRECTION_OPTIONS"] = DIRECTION_OPTIONS
        config["TIME_PERIOD_OPTIONS"] = TIME_PERIOD_OPTIONS
        super().__init__(config)
        
        self.collection_name = "darwin"
        self.chunk_size = "1500"
        self.chunk_overlap = "250"
        self.embedding_model = "Livingwithmachines/bert_1760_1900"
        self._supports_direction_filtering = True
        self._supports_time_period_filtering = True

        # Location of the persisted Chroma DB
        self.persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./create/letters/output/chroma_db")
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model)
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )
        self._retriever = self.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 10})

    def get_retriever(self):
        return self._retriever

    def get_config(self) -> Dict[str, Any]:
        return {
            "collection_name": self.collection_name,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "embedding_model": self.embedding_model,
            "persist_directory": self.persist_directory,
            "supports_direction_filtering": self._supports_direction_filtering,
            "supports_time_period_filtering": self._supports_time_period_filtering,
        }

    @property
    def supports_direction_filtering(self) -> bool:
        return self._supports_direction_filtering
    
    @property
    def supports_time_period_filtering(self) -> bool:
        return self._supports_time_period_filtering

    def get_direction_options(self) -> List[Dict[str, str]]:
        return DIRECTION_OPTIONS
    
    def get_time_period_options(self) -> List[Dict[str, str]]:
        return TIME_PERIOD_OPTIONS

    def _build_filter_dict(self, direction_filter: Optional[str] = None, 
                          time_period_filter: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Build filter dictionary for Chroma search."""
        filter_conditions = []
        
        # Direction filter: sent by Darwin or received by Darwin
        if direction_filter and direction_filter != "all":
            if direction_filter == "sent":
                # Letters sent by Darwin (Darwin is sender)
                filter_conditions.append({"sender_name": "Darwin, C. R."})
            elif direction_filter == "received":
                # Letters received by Darwin (Darwin is recipient)
                filter_conditions.append({"recipient_name": "Darwin, C. R."})
        
        # Time period filter
        if time_period_filter and time_period_filter != "all":
            if "-" in time_period_filter:  # Range like "1850-1870"
                try:
                    start_year, end_year = map(int, time_period_filter.split("-"))
                    filter_conditions.append({"$and": [
                        {"year": {"$gte": start_year}},
                        {"year": {"$lte": end_year}}
                    ]})
                except ValueError:
                    pass
            else:  # Specific year
                try:
                    year = int(time_period_filter)
                    filter_conditions.append({"year": year})
                except ValueError:
                    pass
        
        if filter_conditions:
            if len(filter_conditions) == 1:
                return filter_conditions[0]
            else:
                return {"$and": filter_conditions}
        
        return None

    def similar_search(self, query: str, k: int = 10, 
                      direction_filter: Optional[str] = None,
                      time_period_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar documents with optional filtering."""
        logger.info(f"similar_search: k={k}, direction_filter={direction_filter}, time_period_filter={time_period_filter}")
        
        filter_dict = self._build_filter_dict(direction_filter, time_period_filter)
        
        # Use standard similarity search
        docs = self.vector_store.similarity_search(query=query, k=k, filter=filter_dict)
        return [{
            "id": doc.metadata.get("letter_id", "unknown"),
            "content": doc.page_content,
            "letter_id": doc.metadata.get("letter_id", "unknown"),
            "sender_name": doc.metadata.get("sender_name", "unknown"),
            "recipient_name": doc.metadata.get("recipient_name", "unknown"),
            "sender_place": doc.metadata.get("sender_place", "unknown"),
            "date_sent": doc.metadata.get("date_sent", "unknown"),
            "year": doc.metadata.get("year", "unknown"),
            "abstract": doc.metadata.get("abstract", ""),
            "chunk_index": doc.metadata.get("chunk_index", 0),
            "total_chunks": doc.metadata.get("total_chunks", 1),
            "source_file": doc.metadata.get("source_file", "unknown"),
            "corpus": doc.metadata.get("corpus", "darwin_letters")
        } for doc in docs]
    
    # LangChain-compatible async implementation
    async def _get_relevant_documents(self, query: str, config: Optional[Dict] = None, **kwargs) -> List[Document]:
        """Internal implementation method called by invoke/ainvoke"""
        k = kwargs.get("k", 10)
        direction_filter = None
        time_period_filter = None
        
        # Extract filters from config if present
        if config and isinstance(config, dict):
            direction_filter = config.get("direction_filter")
            time_period_filter = config.get("time_period_filter")
        
        filter_dict = self._build_filter_dict(direction_filter, time_period_filter)
        
        # Use standard similarity search
        return self.vector_store.similarity_search(query=query, k=k, filter=filter_dict)
    
    # Public API methods required by LangChain
    def invoke(self, input: str, config: Optional[Dict] = None, **kwargs) -> List[Document]:
        """Synchronous invoke method required by LangChain."""
        import asyncio
        return asyncio.run(self._get_relevant_documents(input, config, **kwargs))
    
    async def ainvoke(self, input: str, config: Optional[Dict] = None, **kwargs) -> List[Document]:
        """Asynchronous invoke method required by LangChain."""
        return await self._get_relevant_documents(input, config, **kwargs)

# Compatibility helper for citation formatting (imported by streaming.py)
def format_document_for_citation(document: Document, idx: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Convert a Document into the citation structure expected by the frontend."""
    if not document:
        return None

    meta = getattr(document, 'metadata', {}) or {}
    text = getattr(document, 'page_content', str(document))

    preview = text[:300] + ("..." if len(text) > 300 else "")
    doc_id = meta.get("letter_id") or meta.get("id") or (f"letter_{idx}" if idx is not None else "unknown")

    # Create a more informative title for letters
    sender = meta.get("sender_name", "Unknown")
    recipient = meta.get("recipient_name", "Unknown")
    date = meta.get("date_sent", "Unknown date")
    title = f"Letter from {sender} to {recipient} ({date})"

    return {
        "id": doc_id,
        "source_id": doc_id,
        "title": title,
        "url": "",  # Letters don't have URLs
        "date": meta.get("date_sent", ""),
        "sender": meta.get("sender_name", ""),
        "recipient": meta.get("recipient_name", ""),
        "place": meta.get("sender_place", ""),
        "year": meta.get("year", ""),
        "abstract": meta.get("abstract", ""),
        "letter_id": meta.get("letter_id", ""),
        "chunk_index": meta.get("chunk_index", 0),
        "total_chunks": meta.get("total_chunks", 1),
        "corpus": meta.get("corpus", "darwin"),
        "text": preview,
        "quote": preview,
        "content": text,
        "full_content": text,
        "loc": f"Chunk {meta.get('chunk_index', 0) + 1} of {meta.get('total_chunks', 1)}",
        "weight": 1.0,
        "has_more": len(text) > 300,
    }
