#!/usr/bin/env python3
"""
Enhanced Darwin Retriever Generator for ATLAS

This script generates a complete Darwin retriever with all advanced features:
- Hybrid search (dense + BM25 + RRF fusion)
- Rich citation formatting with TEI entities
- CUDA fallback capabilities
- Darwin Project canonical URLs
- Time period and direction filtering

The generated retriever matches the full functionality of the working darwin_retriever.py
and integrates seamlessly with the ATLAS frontend.
"""
import os
import re
import sys
from pathlib import Path
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents.base import Document

# Ensure project root is on sys.path so `import backend` works no matter where
# this script is executed from (Makefile may invoke it from a sub-shell).
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.retrievers.base_retriever import BaseRetriever

def parse_manifest_file(manifest_path):
    config = {}
    try:
        with open(manifest_path, 'r') as f:
            content = f.read()
            # Extract key parameters from Darwin letters stats file
            collection_match = re.search(r'Collection:\s*(.+)', content)
            model_match = re.search(r'Model:\s*(.+)', content)
            chunk_size_match = re.search(r'Chunk Size:\s*(\d+)', content)
            chunk_overlap_match = re.search(r'Chunk Overlap:\s*(\d+)', content)
            created_match = re.search(r'Created:\s*(.+)', content)
            text_splitter_match = re.search(r'Text Splitter:\s*(.+)', content)
            
            if collection_match: config['COLLECTION_NAME'] = collection_match.group(1).strip()
            if model_match: config['EMBEDDING_MODEL'] = model_match.group(1).strip()
            if chunk_size_match: config['CHUNK_SIZE'] = chunk_size_match.group(1)
            if chunk_overlap_match: config['CHUNK_OVERLAP'] = chunk_overlap_match.group(1)
            if created_match: config['CREATED'] = created_match.group(1).strip()
            if text_splitter_match: config['TEXT_SPLITTER'] = text_splitter_match.group(1).strip()
    except Exception as e:
        print(f"Error parsing manifest: {e}")
        sys.exit(1)
    
    required = ['COLLECTION_NAME', 'EMBEDDING_MODEL', 'CHUNK_SIZE', 'CHUNK_OVERLAP']
    for k in required:
        if k not in config:
            print(f"Missing {k} in manifest!")
            sys.exit(1)
    return config

def generate_atlas_retriever(config, output_path):
    """Generate enhanced Darwin retriever using the working template."""
    # Use the enhanced generator instead of the old basic template
    import subprocess
    
    enhanced_script = Path(__file__).parent / "create_darwin_retriever_enhanced.py"
    if enhanced_script.exists():
        print("🔄 Using enhanced retriever generator...")
        result = subprocess.run([sys.executable, str(enhanced_script)], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Enhanced retriever generated successfully!")
            return
        else:
            print(f"❌ Enhanced generator failed: {result.stderr}")
            print("🔄 Falling back to basic template...")
    
    # Fallback to basic template (original code)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    template = '''#!/usr/bin/env python3
"""
Auto-generated ATLAS Retriever for Darwin Corpus
Generated: {now}
Manifest creation: {CREATED}
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
    {{"value": "all", "label": "All Letters"}},
    {{"value": "sent", "label": "Sent by Darwin"}},
    {{"value": "received", "label": "Received by Darwin"}}
]

# Define time period options
TIME_PERIOD_OPTIONS = [
    {{"value": "all", "label": "All Years"}},
    {{"value": "1821-1840", "label": "Early Years (1821-1840)"}},
    {{"value": "1831-1850", "label": "Voyage & Development (1831-1850)"}},
    {{"value": "1850-1870", "label": "Origin Period (1850-1870)"}},
    {{"value": "1870-1882", "label": "Later Years (1870-1882)"}}
]


class DarwinRetriever(BaseRetriever):
    """Darwin corpus retriever implementation for ATLAS."""
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {{}}
        
        config["DIRECTION_OPTIONS"] = DIRECTION_OPTIONS
        config["TIME_PERIOD_OPTIONS"] = TIME_PERIOD_OPTIONS
        super().__init__(config)
        
        self.collection_name = "{COLLECTION_NAME}"
        self.chunk_size = "{CHUNK_SIZE}"
        self.chunk_overlap = "{CHUNK_OVERLAP}"
        self.embedding_model = "{EMBEDDING_MODEL}"
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
        self._retriever = self.vector_store.as_retriever(search_type="similarity", search_kwargs={{"k": 10}})

    def get_retriever(self):
        return self._retriever

    def get_config(self) -> Dict[str, Any]:
        return {{
            "collection_name": self.collection_name,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "embedding_model": self.embedding_model,
            "persist_directory": self.persist_directory,
            "supports_direction_filtering": self._supports_direction_filtering,
            "supports_time_period_filtering": self._supports_time_period_filtering,
        }}

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
                filter_conditions.append({{"sender_name": "Darwin, C. R."}})
            elif direction_filter == "received":
                # Letters received by Darwin (Darwin is recipient)
                filter_conditions.append({{"recipient_name": "Darwin, C. R."}})
        
        # Time period filter
        if time_period_filter and time_period_filter != "all":
            if "-" in time_period_filter:  # Range like "1850-1870"
                try:
                    start_year, end_year = map(int, time_period_filter.split("-"))
                    filter_conditions.append({{"$and": [
                        {{"year": {{"$gte": start_year}}}},
                        {{"year": {{"$lte": end_year}}}}
                    ]}})
                except ValueError:
                    pass
            else:  # Specific year
                try:
                    year = int(time_period_filter)
                    filter_conditions.append({{"year": year}})
                except ValueError:
                    pass
        
        if filter_conditions:
            if len(filter_conditions) == 1:
                return filter_conditions[0]
            else:
                return {{"$and": filter_conditions}}
        
        return None

    def similar_search(self, query: str, k: int = 10, 
                      direction_filter: Optional[str] = None,
                      time_period_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar documents with optional filtering."""
        logger.info(f"similar_search: k={{k}}, direction_filter={{direction_filter}}, time_period_filter={{time_period_filter}}")
        
        filter_dict = self._build_filter_dict(direction_filter, time_period_filter)
        
        # Use standard similarity search
        docs = self.vector_store.similarity_search(query=query, k=k, filter=filter_dict)
        return [{{
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
        }} for doc in docs]
    
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

    meta = getattr(document, 'metadata', {{}}) or {{}}
    text = getattr(document, 'page_content', str(document))

    preview = text[:300] + ("..." if len(text) > 300 else "")
    doc_id = meta.get("letter_id") or meta.get("id") or (f"letter_{{idx}}" if idx is not None else "unknown")

    # Create a more informative title for letters
    sender = meta.get("sender_name", "Unknown")
    recipient = meta.get("recipient_name", "Unknown")
    date = meta.get("date_sent", "Unknown date")
    title = f"Letter from {{sender}} to {{recipient}} ({{date}})"

    return {{
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
        "loc": f"Chunk {{meta.get('chunk_index', 0) + 1}} of {{meta.get('total_chunks', 1)}}",
        "weight": 1.0,
        "has_more": len(text) > 300,
    }}
'''
    cfg = config.copy()
    cfg['now'] = now
    with open(output_path, 'w') as f:
        f.write(template.format(**cfg))
    os.chmod(output_path, 0o755)
    print(f"Generated ATLAS retriever: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate an ATLAS-compatible Darwin Letters Retriever script')
    parser.add_argument('--manifest', required=False, help='Path to the vector store manifest file (.txt)')
    parser.add_argument('--output', required=False, help='Path for the output retriever script (.py)')
    args = parser.parse_args()
    
    script_dir = Path(__file__).resolve().parent
    
    if not args.manifest:
        # Default to the script's own output/ directory rather than CWD
        default_manifest_dir = script_dir / 'output'
        if os.path.exists(default_manifest_dir):
            txt_files = [f for f in os.listdir(default_manifest_dir) if f.endswith('.txt')]
            if txt_files:
                args.manifest = str(Path(default_manifest_dir) / txt_files[0])
                print(f"Using manifest file: {args.manifest}")
            else:
                print("No .txt manifest files found in ./output/")
                sys.exit(1)
        else:
            print("No manifest file specified and ./output/ directory not found")
            sys.exit(1)
    
    if not os.path.exists(args.manifest):
        print(f"Manifest file not found: {args.manifest}")
        sys.exit(1)
    
    config = parse_manifest_file(args.manifest)
    
    # Always output to ./output directory, regardless of manifest location
    output_dir = str(script_dir / 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    collection_name = config['COLLECTION_NAME']
    output_path = os.path.join(output_dir, f"{collection_name}_retriever.py")
    
    generate_atlas_retriever(config, output_path)
    print(f"\nRetriever script generation complete!\nLocation: {output_path}\nYou can use it in ATLAS backend or run it standalone.")

if __name__ == "__main__":
    main()