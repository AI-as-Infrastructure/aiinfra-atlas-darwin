#!/usr/bin/env python3
"""
Darwin Retriever with hybrid search (dense + BM25 via RRF).
"""
import os
import logging
import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents.base import Document

from backend.retrievers.base_retriever import BaseRetriever
from backend.modules.hybrid_search import rrf_merge

try:
    from rank_bm25 import BM25Okapi
except Exception:
    BM25Okapi = None

logger = logging.getLogger(__name__)
TOKEN_RE = re.compile(r"\b\w+\b", re.UNICODE)

# Direction/time filters for UI
DIRECTION_OPTIONS = [
    {"value": "all", "label": "All Letters"},
    {"value": "sent", "label": "Sent by Darwin"},
    {"value": "received", "label": "Received by Darwin"},
]

TIME_PERIOD_OPTIONS = [
    {"value": "all", "label": "All Years"},
    {"value": "1821-1840", "label": "1821-1840"},
    {"value": "1831-1850", "label": "1831-1850"},
    {"value": "1850-1870", "label": "1850-1870"},
    {"value": "1870-1882", "label": "1870-1882"},
]


class DarwinRetriever(BaseRetriever):
    """Darwin corpus retriever implementation for ATLAS with hybrid search."""

    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
        config["DIRECTION_OPTIONS"] = DIRECTION_OPTIONS
        config["TIME_PERIOD_OPTIONS"] = TIME_PERIOD_OPTIONS
        super().__init__(config)

        # Core config
        self.collection_name = "darwin"
        self.chunk_size = "1500"
        self.chunk_overlap = "250"
        self.embedding_model = "Livingwithmachines/bert_1760_1900"
        self._supports_direction_filtering = True
        self._supports_time_period_filtering = True

        # Vector store
        self.persist_directory = os.getenv(
            "CHROMA_PERSIST_DIRECTORY", "./create/Darwin/xml/output/chroma_db"
        )
        self._initialize_vector_store()

        # Hybrid search
        self.default_search_type = os.getenv("DARWIN_SEARCH_TYPE", "hybrid")
        self._bm25_ready = False
        self._bm25 = None
        self._bm25_docs = []
        self._bm25_docid_to_idx = {}
        self._maybe_initialize_bm25()

    def _initialize_vector_store(self):
        # Try GPU first, fall back to CPU if CUDA fails
        model_kwargs = {"device": "cuda"}
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs=model_kwargs
            )
        except RuntimeError as e:
            if "CUDA" in str(e):
                model_kwargs = {"device": "cpu"}
                self.embeddings = HuggingFaceEmbeddings(
                    model_name=self.embedding_model,
                    model_kwargs=model_kwargs
                )
            else:
                raise
        
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )
        self._retriever = self.vector_store.as_retriever(
            search_type="similarity", search_kwargs={"k": 10}
        )

    def _maybe_initialize_bm25(self):
        if self._bm25_ready or BM25Okapi is None:
            return
        try:
            default_path = Path("create/Darwin/xml/output/bm25_corpus.jsonl")
            corpus_path = Path(os.getenv("DARWIN_BM25_CORPUS", str(default_path)))
            if not corpus_path.exists():
                logger.warning(
                    f"BM25 corpus not found: {corpus_path} (dense-only mode)"
                )
                return

            texts = []
            with corpus_path.open("r", encoding="utf-8") as fh:
                for i, line in enumerate(fh):
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    self._bm25_docs.append(rec)
                    self._bm25_docid_to_idx[rec["id"]] = i
                    tokens = [t.lower() for t in TOKEN_RE.findall(rec.get("text", ""))]
                    texts.append(tokens)

            if not texts:
                logger.warning("BM25 corpus empty; dense-only mode")
                return

            self._bm25 = BM25Okapi(texts)
            self._bm25_ready = True
            logger.info(f"BM25 index loaded with {len(self._bm25_docs)} docs")
        except Exception as e:
            logger.warning(f"BM25 init failed: {e} (dense-only mode)")

    def _unique_id_from_meta(self, meta: Dict[str, Any]) -> str:
        return f"{meta.get('letter_id','unknown')}#{meta.get('chunk_index',0)}"

    def _build_filter_dict(
        self, direction_filter: Optional[str] = None, time_period_filter: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        filter_conditions: List[Dict[str, Any]] = []
        if direction_filter and direction_filter != "all":
            if direction_filter == "sent":
                filter_conditions.append({"sender_name": "Darwin, C. R."})
            elif direction_filter == "received":
                filter_conditions.append({"recipient_name": "Darwin, C. R."})

        if time_period_filter and time_period_filter != "all":
            if "-" in time_period_filter:
                try:
                    start_year, end_year = map(int, time_period_filter.split("-"))
                    filter_conditions.append(
                        {
                            "$and": [
                                {"year": {"$gte": start_year}},
                                {"year": {"$lte": end_year}},
                            ]
                        }
                    )
                except ValueError:
                    pass
            else:
                try:
                    year = int(time_period_filter)
                    filter_conditions.append({"year": year})
                except ValueError:
                    pass

        if filter_conditions:
            if len(filter_conditions) == 1:
                return filter_conditions[0]
            return {"$and": filter_conditions}
        return None

    def _dense_search_docs(
        self, query: str, k: int, filter_dict: Optional[Dict[str, Any]]
    ) -> List[Document]:
        try:
            return self.vector_store.similarity_search(query=query, k=k, filter=filter_dict)
        except RuntimeError as e:
            if "CUDA" in str(e):
                # Re-initialize with CPU if CUDA fails at query time
                self._initialize_vector_store_cpu()
                return self.vector_store.similarity_search(query=query, k=k, filter=filter_dict)
            else:
                raise
    
    def _initialize_vector_store_cpu(self):
        """Re-initialize vector store with CPU-only embeddings"""
        model_kwargs = {"device": "cpu"}
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            model_kwargs=model_kwargs
        )
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )
        self._retriever = self.vector_store.as_retriever(
            search_type="similarity", search_kwargs={"k": 10}
        )

    def _dense_search_ids(
        self, query: str, k: int, filter_dict: Optional[Dict[str, Any]]
    ) -> List[Tuple[str, float]]:
        docs = self._dense_search_docs(query, k, filter_dict)
        return [
            (self._unique_id_from_meta(getattr(d, "metadata", {})), float(i))
            for i, d in enumerate(docs)
        ]

    def _bm25_search_ids(self, query: str, k: int) -> List[Tuple[str, float]]:
        if not self._bm25_ready:
            return []
        tokens = [t.lower() for t in TOKEN_RE.findall(query)]
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]
        out: List[Tuple[str, float]] = []
        for rank_pos, (idx, _score) in enumerate(ranked):
            doc_id = self._bm25_docs[idx]["id"]
            out.append((doc_id, float(rank_pos)))
        return out

    def _materialize_docs_by_ids(
        self, ids: List[str], filter_dict: Optional[Dict[str, Any]]
    ) -> List[Document]:
        result: List[Document] = []
        for doc_id in ids:
            idx = self._bm25_docid_to_idx.get(doc_id)
            if idx is None:
                continue
            rec = self._bm25_docs[idx]
            meta = rec.get("metadata", {})
            # Minimal filter enforcement for known fields
            if filter_dict and isinstance(filter_dict, dict):
                if "sender_name" in filter_dict and meta.get("sender_name") != filter_dict["sender_name"]:
                    continue
                if "recipient_name" in filter_dict and meta.get("recipient_name") != filter_dict["recipient_name"]:
                    continue
                if "$and" in filter_dict:
                    ok = True
                    for cond in filter_dict["$and"]:
                        if "year" in cond and isinstance(cond["year"], dict):
                            y = meta.get("year")
                            if y is None:
                                ok = False
                                break
                            if "$gte" in cond["year"] and y < cond["year"]["$gte"]:
                                ok = False
                                break
                            if "$lte" in cond["year"] and y > cond["year"]["$lte"]:
                                ok = False
                                break
                    if not ok:
                        continue
                elif "year" in filter_dict and isinstance(filter_dict["year"], int):
                    if meta.get("year") != filter_dict["year"]:
                        continue

            result.append(Document(page_content=rec.get("text", ""), metadata=meta))
        return result

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

    @property
    def supports_corpus_filtering(self) -> bool:
        return False

    def get_corpus_options(self) -> List[Dict[str, str]]:
        return []

    def get_direction_options(self) -> List[Dict[str, str]]:
        return DIRECTION_OPTIONS

    def get_time_period_options(self) -> List[Dict[str, str]]:
        return TIME_PERIOD_OPTIONS

    def similar_search(
        self,
        query: str,
        k: int = 10,
        direction_filter: Optional[str] = None,
        time_period_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        logger.info(
            f"similar_search: k={k}, direction_filter={direction_filter}, time_period_filter={time_period_filter}"
        )
        filter_dict = self._build_filter_dict(direction_filter, time_period_filter)
        docs = self.vector_store.similarity_search(query=query, k=k, filter=filter_dict)
        return [
            {
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
                "corpus": doc.metadata.get("corpus", "darwin_letters"),
            }
            for doc in docs
        ]

    async def _get_relevant_documents(
        self, query: str, config: Optional[Dict] = None, **kwargs
    ) -> List[Document]:
        k = kwargs.get("k", 10)
        direction_filter = None
        time_period_filter = None
        if config and isinstance(config, dict):
            direction_filter = config.get("direction_filter")
            time_period_filter = config.get("time_period_filter")
        filter_dict = self._build_filter_dict(direction_filter, time_period_filter)
        search_type = (
            (config or {}).get("search_type")
            or (self.config or {}).get("search_type", self.default_search_type)
        )
        if search_type == "hybrid" and self._bm25_ready:
            per_side = max(k * 10, 100)
            dense_ranked = self._dense_search_ids(query, per_side, filter_dict)
            bm25_ranked = self._bm25_search_ids(query, per_side)
            if not dense_ranked and not bm25_ranked:
                return []
            fused_ids = rrf_merge(dense_ranked, bm25_ranked, k=60, top_k=k)
            return self._materialize_docs_by_ids(fused_ids, filter_dict)
        return self.vector_store.similarity_search(query=query, k=k, filter=filter_dict)

    def invoke(self, input: str, config: Optional[Dict] = None, **kwargs) -> List[Document]:
        # Synchronous hybrid search implementation
        k = kwargs.get("k", 10)
        direction_filter = None
        time_period_filter = None
        if config and isinstance(config, dict):
            direction_filter = config.get("direction_filter")
            time_period_filter = config.get("time_period_filter")
        filter_dict = self._build_filter_dict(direction_filter, time_period_filter)
        search_type = (
            (config or {}).get("search_type")
            or (self.config or {}).get("search_type", self.default_search_type)
        )
        
        if search_type == "hybrid" and self._bm25_ready:
            per_side = max(k * 10, 100)
            dense_ranked = self._dense_search_ids(input, per_side, filter_dict)
            bm25_ranked = self._bm25_search_ids(input, per_side)
            if not dense_ranked and not bm25_ranked:
                return []
            fused_ids = rrf_merge(dense_ranked, bm25_ranked, k=60, top_k=k)
            return self._materialize_docs_by_ids(fused_ids, filter_dict)
        
        return self.vector_store.similarity_search(query=input, k=k, filter=filter_dict)

    async def ainvoke(self, input: str, config: Optional[Dict] = None, **kwargs) -> List[Document]:
        return await self._get_relevant_documents(input, config, **kwargs)


def format_document_for_citation(document: Document, idx: Optional[int] = None) -> Optional[Dict[str, Any]]:
        if not document:
            return None
        meta = getattr(document, "metadata", {}) or {}
        text = getattr(document, "page_content", str(document))
        preview = text[:300] + ("..." if len(text) > 300 else "")
        doc_id = meta.get("letter_id") or meta.get("id") or (
            f"letter_{idx}" if idx is not None else "unknown"
        )
        sender = meta.get("sender_name", "Unknown")
        recipient = meta.get("recipient_name", "Unknown")
        date = meta.get("date_sent", "Unknown date")
        title = f"Letter from {sender} to {recipient} ({date})"
        # Canonical DarwinProject URL (when we have a proper letter_id)
        letter_id = meta.get("letter_id") or doc_id
        canonical_url = ""
        if isinstance(letter_id, str) and letter_id.startswith("DCP-LETT-"):
            canonical_url = f"https://www.darwinproject.ac.uk/letter/?docId=letters/{letter_id}.xml"
        # Recommended citation e.g., Darwin Correspondence Project, “Letter no. 4747F,” https://...
        letter_no = None
        if isinstance(letter_id, str) and letter_id.startswith("DCP-LETT-"):
            letter_no = letter_id.replace("DCP-LETT-", "")
        recommended_citation = None
        if letter_no and canonical_url:
            recommended_citation = f"Darwin Correspondence Project, \"Letter no. {letter_no},\" {canonical_url}"

        citation = {
            "id": doc_id,
            "source_id": doc_id,
            "title": title,
            "url": canonical_url,
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
            "recommended_citation": recommended_citation,
            # TEI entity badges for UI filters/hover (parse from semicolon-separated strings)
            "entities": {
                "persons": meta.get("tei_persons", "").split(";") if meta.get("tei_persons") else [],
                "places": meta.get("tei_places", "").split(";") if meta.get("tei_places") else [],
                "orgs": meta.get("tei_orgs", "").split(";") if meta.get("tei_orgs") else [],
                "taxa": meta.get("tei_taxa", "").split(";") if meta.get("tei_taxa") else [],
            },
            "text": preview,
            "quote": preview,
            "content": text,
            "full_content": text,
            "loc": f"Chunk {meta.get('chunk_index', 0) + 1} of {meta.get('total_chunks', 1)}",
            "truncation_notice": "This excerpt is from a larger document. For the complete letter, consult the canonical version at the Darwin Correspondence Project.",
            "weight": 1.0,
            "has_more": len(text) > 300,
        }
        # Attach bibliographic references when present
        if meta.get("tei_bibl") or meta.get("tei_bibl_struct"):
            citation["bibliography"] = {
                "bibl": meta.get("tei_bibl", []),
                "bibl_struct": meta.get("tei_bibl_struct", []),
            }
        return citation
