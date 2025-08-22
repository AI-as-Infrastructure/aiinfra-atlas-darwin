"""
Citation aggregation utilities.

Goal: collapse chunk-level documents into parent-level citations so the UI
shows a manageable number of sources (e.g., per letter), even when many
chunks are retrieved.
"""
from typing import List, Dict, Any, Optional

try:
    from langchain_core.documents.base import Document
except Exception:  # pragma: no cover - type-only convenience
    class Document:  # minimal stub
        page_content: str
        metadata: Dict[str, Any]


def _preview(text: str, max_len: int = 300) -> str:
    return text[:max_len] + ("..." if len(text) > max_len else "")


def aggregate_parent_citations(
    documents: List[Document],
    *,
    parent_key: str = "letter_id",
    limit: int = 10,
    formatter_fn: Optional[callable] = None,
) -> List[Dict[str, Any]]:
    """
    Group documents by parent (e.g., letter_id) and emit one citation per parent.

    - Preserves first-seen order of parents (respects ranking already applied).
    - Uses the first chunk in each group as the representative for the citation
      and augments with chunk indices, total_chunks, and short previews.
    - If formatter_fn is provided, it's used to build the base citation dict
      from the representative Document; otherwise a minimal fallback is used.
    """
    if not documents:
        return []

    # Index by parent, preserving order of first appearance
    groups: Dict[str, List[Document]] = {}
    order: List[str] = []
    for doc in documents:
        meta = getattr(doc, "metadata", {}) or {}
        parent_id = meta.get(parent_key)
        if not parent_id:
            # If any doc lacks the parent key, skip aggregation entirely
            return []
        if parent_id not in groups:
            groups[parent_id] = []
            order.append(parent_id)
        groups[parent_id].append(doc)

    # Build citations up to the limit
    citations: List[Dict[str, Any]] = []
    for parent_id in order[:limit]:
        docs = groups[parent_id]
        rep = docs[0]
        meta = getattr(rep, "metadata", {}) or {}
        text = getattr(rep, "page_content", str(rep))

    # Use provided formatter when available
        base: Dict[str, Any]
        if formatter_fn is not None:
            try:
                base = formatter_fn(rep, 0) or {}
            except Exception:
                base = {}
        else:
            # Minimal fallback structure
            # Build a canonical URL if possible
            letter_id = meta.get("letter_id") or meta.get("id") or parent_id
            canonical_url = ""
            if isinstance(letter_id, str) and letter_id.startswith("DCP-LETT-"):
                canonical_url = f"https://www.darwinproject.ac.uk/letter/?docId=letters/{letter_id}.xml"
            letter_no = letter_id.replace("DCP-LETT-", "") if isinstance(letter_id, str) and letter_id.startswith("DCP-LETT-") else None
            recommended_citation = f"Darwin Correspondence Project, \"Letter no. {letter_no},\" {canonical_url}" if letter_no and canonical_url else None

            base = {
                "id": meta.get("letter_id") or meta.get("id") or parent_id,
                "source_id": meta.get("letter_id") or meta.get("id") or parent_id,
                "title": meta.get(
                    "title",
                    f"Letter from {meta.get('sender_name','Unknown')} to {meta.get('recipient_name','Unknown')} ({meta.get('date_sent','')})",
                ),
                "url": canonical_url or meta.get("url", ""),
                "date": meta.get("date_sent", ""),
                "corpus": meta.get("corpus", ""),
                "recommended_citation": recommended_citation,
                "text": _preview(text),
                "quote": _preview(text),
                "content": text,
                "full_content": text,
            }

        # Aggregate chunk indices and total
        chunk_indices = [m.get("chunk_index", 0) for m in (getattr(d, "metadata", {}) or {} for d in docs)]
        try:
            total_chunks = max((getattr(d, "metadata", {}) or {}).get("total_chunks", 1) for d in docs)
        except Exception:
            total_chunks = (getattr(rep, "metadata", {}) or {}).get("total_chunks", 1)

        # Optionally collect a couple of additional previews
        extras = []
        for d in docs[1:3]:  # up to 2 additional snippets
            extras.append(_preview(getattr(d, "page_content", str(d))))

        # Decorate base with aggregation details and TEI entity badges when available
        entities = {
            "persons": meta.get("tei_persons", []),
            "places": meta.get("tei_places", []),
            "orgs": meta.get("tei_orgs", []),
            "taxa": meta.get("tei_taxa", []),
        }
        chunk_set = sorted(set(chunk_indices))
        loc_summary = f"Chunks {', '.join(str(i+1) for i in chunk_set[:3])}{'…' if len(chunk_set)>3 else ''} of {total_chunks}"
        base.update(
            {
                "parent_id": parent_id,
                "letter_id": parent_id,
                "chunk_indices": chunk_set,
                "total_chunks": total_chunks,
                "loc": loc_summary,
                "related_snippets": extras,
                "entities": entities,
            }
        )

        citations.append(base)

    return citations
