#!/usr/bin/env python3

# create_darwin_store.py
# Creates a Chroma vector store for Darwin corpus (letters, books, etc.) with document-level chunking and metadata.

# Ensure project root on path *before* any local package imports
import sys, os
from pathlib import Path
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Standard libs
import re, json, time, subprocess, shutil
import platform
try:
    import psutil  # type: ignore
except Exception:
    psutil = None
from dotenv import load_dotenv
try:
    from tqdm import tqdm  # type: ignore
except Exception:
    def tqdm(x, **kwargs):
        return x

# Heavy ML deps (optional in lexical-only runs)
try:
    import numpy as np  # type: ignore
except Exception:
    np = None
try:
    import torch  # type: ignore
except Exception:
    torch = None
try:
    from transformers import AutoTokenizer, AutoModel, AutoConfig  # type: ignore
except Exception:
    AutoTokenizer = AutoModel = AutoConfig = None

# LangChain deps (only needed when not lexical-only)
try:
    from langchain_community.vectorstores import Chroma  # type: ignore
    from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter  # type: ignore
    from langchain_huggingface import HuggingFaceEmbeddings  # type: ignore
    from langchain.schema import Document  # type: ignore
except Exception:
    Chroma = RecursiveCharacterTextSplitter = CharacterTextSplitter = HuggingFaceEmbeddings = Document = None
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime
from bs4 import BeautifulSoup
import csv
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from prepare_embedding_model import ensure_st_model
from chromadb import PersistentClient
from chromadb.config import Settings

# -------------------------------------------------------------
# Load environment variables (development, staging, production)
# -------------------------------------------------------------

repo_root = Path(__file__).resolve().parents[2]  # project root
env_candidates = [
    repo_root / "config" / ".env.development",
    repo_root / "config" / ".env.staging",
    repo_root / "config" / ".env.production",
]

for _env in env_candidates:
    if _env.exists():
        print(f"Loading environment variables from: {_env}")
        load_dotenv(dotenv_path=_env, override=False)
        break
else:
    print("[WARN] No .env.* file found under config/. Proceeding with current environment.")

# Download NLTK data (best-effort)
try:
    import nltk  # type: ignore
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
    except Exception as e:
        print(f"Warning: NLTK data download failed: {e}")
except Exception:
    nltk = None

# Data paths from .env configuration
DEFAULT_FULL_XML = os.getenv("DARWIN_XML_FULL_PATH", "../../../../darwin_sources_FULL/xml/letters")
DEFAULT_TEST_XML = os.getenv("DARWIN_XML_TEST_PATH", "../../../../darwin_sources_TEST/xml/letters")
DEFAULT_CSV = os.getenv("DARWIN_CSV_PATH", "../../../../darwin_sources_FULL/csv/darwin-correspondence.csv")

# Allow runtime overrides via legacy environment variables
LETTERS_XML_DIR = os.getenv("DARWIN_LETTERS_XML_DIR", DEFAULT_FULL_XML)
LETTERS_CSV_PATH = os.getenv("DARWIN_LETTERS_CSV_PATH", DEFAULT_CSV)

# Resolve paths and apply TEST fallback for XML if FULL path isn't present
def _choose_letters_dir(path: str) -> str:
    try:
        # If already absolute, Path will normalize; otherwise treat relative to script
        abs_candidate = str((Path(__file__).resolve().parent / path).resolve())
        if os.path.isdir(abs_candidate):
            print(f"Using letters XML directory: {abs_candidate}")
            return abs_candidate
    except Exception:
        pass
    # Try a direct check (handles when env provided an absolute path)
    if os.path.isdir(path):
        print(f"Using letters XML directory: {path}")
        return path
    # Fallback to TEST if available
    test_path = resolve_path(DEFAULT_TEST_XML)
    if os.path.isdir(test_path):
        print(f"[INFO] Falling back to TEST letters XML directory: {test_path}")
        return test_path
    print(f"[ERROR] Letters XML directory not found: {path}")
    return path

LETTERS_XML_DIR = _choose_letters_dir(LETTERS_XML_DIR)

# CSV is optional; warn if missing rather than failing
def _resolve_optional_csv(path: str) -> str:
    try:
        abs_candidate = str((Path(__file__).resolve().parent / path).resolve())
        if os.path.isfile(abs_candidate):
            print(f"Using letters CSV: {abs_candidate}")
            return abs_candidate
    except Exception:
        pass
    if os.path.isfile(path):
        print(f"Using letters CSV: {path}")
        return path
    print(f"[WARN] Letters CSV not found, proceeding without: {path}")
    return path

LETTERS_CSV_PATH = _resolve_optional_csv(LETTERS_CSV_PATH)

# Helper to resolve relative paths based on this script's directory
def resolve_path(relative_path):
    """Resolve a relative or absolute path against this script's directory."""
    script_dir = Path(__file__).resolve().parent
    try:
        # If relative_path is absolute, Path.join will ignore the left side
        return str((script_dir / relative_path).resolve())
    except Exception:
        return relative_path

def get_vector_store_config():
    """Get vector store configuration from environment variables."""
    collection_name = os.getenv('CHROMA_COLLECTION_NAME', 'darwin')
    
    # Get chunking configuration from .env
    chunk_size = int(os.getenv('CHUNK_SIZE', '1500'))
    chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '250'))
    text_splitter_type = os.getenv('TEXT_SPLITTER_TYPE', 'RecursiveCharacterTextSplitter')
    
    config = {
        'COLLECTION_NAME': collection_name,
        'CHUNK_SIZE': chunk_size,
        'CHUNK_OVERLAP': chunk_overlap,
        'TEXT_SPLITTER_TYPE': text_splitter_type
    }
    
    print(f"Vector store config from .env: chunk_size={chunk_size}, overlap={chunk_overlap}, splitter={text_splitter_type}")
    return config

# Get configuration from .env
vector_config = get_vector_store_config()
COLLECTION_NAME = vector_config['COLLECTION_NAME']
CHUNK_SIZE = vector_config['CHUNK_SIZE']
CHUNK_OVERLAP = vector_config['CHUNK_OVERLAP']
TEXT_SPLITTER_TYPE = vector_config['TEXT_SPLITTER_TYPE']

# Other environment variables
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'Livingwithmachines/bert_1760_1900')
POOLING = os.getenv('POOLING', 'mean').lower()
BATCH_SIZE = 100
# Enable a fast pass that only produces a BM25 corpus (no embeddings / Chroma)
LEXICAL_ONLY = os.getenv('DARWIN_LEXICAL_ONLY', os.getenv('LEXICAL_ONLY', 'false')).lower() in ('1', 'true', 'yes')
# Minimum chunk length to include (auto-0 for TEST letters unless overridden)
_min_env = os.getenv('DARWIN_MIN_CHUNK_LEN')
if _min_env is not None:
    MIN_CHUNK_LEN = int(_min_env)
else:
    MIN_CHUNK_LEN = 0 if 'darwin_sources_TEST' in str(LETTERS_XML_DIR) else 50

# Define output directories
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
OUTPUT_CHROMA_DIR = os.path.join(OUTPUT_DIR, "chroma_db")
BM25_CORPUS_PATH = os.path.join(OUTPUT_DIR, "bm25_corpus.jsonl")

# Get Chroma directory from environment variable
FINAL_CHROMA_DIR = os.environ.get("CHROMA_PERSIST_DIRECTORY", OUTPUT_CHROMA_DIR)

# Statistics tracking
letter_stats = {
    'total_letters': 0,
    'total_chunks': 0,
    'total_chars': 0,
    'total_words': 0,
    'skipped_letters': 0,
    'successful_batches': 0
}

def ensure_chroma_directory(chroma_dir):
    """Ensure the Chroma directory exists and is empty."""
    try:
        if os.path.exists(chroma_dir):
            # Clear existing directory
            shutil.rmtree(chroma_dir)
        
        # Create fresh directory
        os.makedirs(chroma_dir, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error preparing Chroma directory: {e}")
        return False

class _MinimalSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = max(1, int(chunk_size))
        self.chunk_overlap = max(0, int(chunk_overlap))
        self.step = max(1, self.chunk_size - self.chunk_overlap)

    def split_text(self, text: str):
        if not text:
            return []
        chunks = []
        i = 0
        n = len(text)
        while i < n:
            chunks.append(text[i:i + self.chunk_size])
            i += self.step
        return chunks

def get_text_splitter(splitter_type, chunk_size, chunk_overlap):
    try:
        if RecursiveCharacterTextSplitter is not None and splitter_type == 'RecursiveCharacterTextSplitter':
            # Enhanced separators for letters - prioritize logical breaks
            letter_separators = [
                "\n\n\n",  # Multiple line breaks (major sections)
                "\n\n",    # Double line breaks (paragraphs)
                "\n",      # Single line breaks
                ". ",      # Sentence endings
                "! ",      # Exclamations
                "? ",      # Questions
                "; ",      # Semicolons (common in Victorian writing)
                ", ",      # Commas
                " ",       # Spaces
                ""         # Characters
            ]
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, 
                chunk_overlap=chunk_overlap,
                separators=letter_separators,
                keep_separator=True,
                is_separator_regex=False
            )
        if CharacterTextSplitter is not None and splitter_type == 'CharacterTextSplitter':
            return CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    except Exception:
        pass
    # Fallback minimal splitter
    return _MinimalSplitter(chunk_size, chunk_overlap)

def clean_letter_text(text):
    """Clean and normalize letter text for better chunking."""
    if not text:
        return text
    
    # Normalize whitespace while preserving paragraph structure
    # Replace multiple spaces with single spaces
    text = re.sub(r' +', ' ', text)
    
    # Normalize line breaks - preserve paragraph breaks
    # Multiple consecutive newlines become double newlines (paragraph breaks)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Single newlines with content on both sides become spaces (unless they're at sentence boundaries)
    # This handles cases where lines are broken mid-sentence
    text = re.sub(r'(?<![.!?:])\n(?=[a-z])', ' ', text)
    
    # Ensure proper spacing after punctuation
    text = re.sub(r'([.!?;:])([A-Z])', r'\1 \2', text)
    
    # Remove excessive whitespace at start/end but preserve internal structure
    text = text.strip()
    
    return text

def parse_letter_xml(xml_file_path):
    """Parse a Darwin letter XML file and extract metadata and content."""
    try:
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'xml')
        
        # Extract letter ID from filename or XML
        letter_id = None
        xml_id = soup.TEI.get('xml:id') if soup.TEI else None
        if xml_id:
            letter_id = xml_id
        else:
            # Extract from filename
            filename = os.path.basename(xml_file_path)
            match = re.search(r'DCP-LETT-(\d+)', filename)
            if match:
                letter_id = f"DCP-LETT-{match.group(1)}"
        
        # Extract correspondence actions
        sender_name = None
        recipient_name = None
        sender_place = None
        date_sent = None
        
        corr_actions = soup.find_all("correspAction")
        for action in corr_actions:
            if action.get('type') == "sent":
                if action.persName:
                    sender_name = action.persName.get_text(strip=True)
                if action.placeName:
                    sender_place = action.placeName.get_text(strip=True)
                if action.date:
                    date_sent = action.date.get('when', action.date.get_text(strip=True))
            elif action.get('type') == "received":
                if action.persName:
                    recipient_name = action.persName.get_text(strip=True)
        
        # Extract abstract/summary
        abstract = None
        abstract_elem = soup.find("abstract")
        if abstract_elem:
            abstract = abstract_elem.get_text(strip=True)
        
        # Extract transcription text
        transcription = None
        transcription_div = soup.find("div", type="transcription")
        if transcription_div:
            transcription = transcription_div.get_text(strip=True)
        
        # If no transcription div, try to get text from body
        if not transcription:
            body = soup.find("body")
            if body:
                transcription = body.get_text(strip=True)
        
        if not transcription:
            return None  # Skip letters without transcription
        
        # Clean and normalize the transcription for better chunking
        transcription = clean_letter_text(transcription)

        # TEI entity enrichment for better lexical search later
        tei_persons, tei_places, tei_orgs, tei_taxa = [], [], [], []
        tei_bibl, tei_bibl_struct = [], []
        try:
            tei_persons = [p.get_text(strip=True) for p in soup.find_all(["persName", "person"]) if p.get_text(strip=True)]
            tei_places = [p.get_text(strip=True) for p in soup.find_all(["placeName", "place"]) if p.get_text(strip=True)]
            tei_orgs = [o.get_text(strip=True) for o in soup.find_all(["orgName", "org"]) if o.get_text(strip=True)]
            tei_taxa = [t.get_text(strip=True) for t in soup.find_all("name") if t.get("type") in ("taxon", "species", "genus", "family") and t.get_text(strip=True)]

            # Bibliographic references (free-text bibl)
            for b in soup.find_all("bibl"):
                txt = b.get_text(" ", strip=True)
                if txt:
                    tei_bibl.append(txt)

            # Structured bibliographic references (biblStruct)
            for bs in soup.find_all("biblStruct"):
                entry = {}
                try:
                    # Authors
                    authors = []
                    for a in bs.find_all(["author", "editor"]):
                        a_txt = a.get_text(" ", strip=True)
                        if a_txt:
                            authors.append(a_txt)
                    if authors:
                        entry["authors"] = authors

                    # Title(s)
                    title = None
                    title_el = bs.find("title")
                    if title_el:
                        title = title_el.get_text(" ", strip=True)
                    if title:
                        entry["title"] = title

                    # Date
                    date_el = bs.find("date")
                    if date_el:
                        entry["date"] = date_el.get("when") or date_el.get_text(strip=True)

                    # Publisher / Imprint
                    imprint = bs.find("imprint")
                    if imprint:
                        pub = imprint.find("publisher")
                        if pub and pub.get_text(strip=True):
                            entry["publisher"] = pub.get_text(strip=True)
                        place = imprint.find("pubPlace")
                        if place and place.get_text(strip=True):
                            entry["pub_place"] = place.get_text(strip=True)

                    # IDs
                    idnos = [i.get_text(strip=True) for i in bs.find_all("idno") if i.get_text(strip=True)]
                    if idnos:
                        entry["ids"] = idnos

                    # Fallback full text
                    if not entry:
                        entry["text"] = bs.get_text(" ", strip=True)

                    tei_bibl_struct.append(entry)
                except Exception:
                    # Best-effort; skip bad entry
                    pass
        except Exception:
            pass
        
        # Parse date to extract year
        year = None
        if date_sent:
            try:
                # Try to extract year from date
                year_match = re.search(r'(\d{4})', date_sent)
                if year_match:
                    year = int(year_match.group(1))
            except:
                pass
        
        return {
            'letter_id': letter_id,
            'sender_name': sender_name,
            'recipient_name': recipient_name,
            'sender_place': sender_place,
            'date_sent': date_sent,
            'year': year,
            'abstract': abstract,
            'transcription': transcription,
            'source_file': xml_file_path,
            # TEI enrichments
            'tei_persons': tei_persons,
            'tei_places': tei_places,
            'tei_orgs': tei_orgs,
            'tei_taxa': tei_taxa,
            # TEI bibliographic references
            'tei_bibl': tei_bibl,
            'tei_bibl_struct': tei_bibl_struct
        }
        
    except Exception as e:
        print(f"Error parsing {xml_file_path}: {e}")
        return None

def load_csv_metadata():
    """Load additional metadata from CSV file."""
    csv_metadata = {}
    csv_path = resolve_path(LETTERS_CSV_PATH)
    
    if not os.path.exists(csv_path):
        print(f"Warning: CSV file not found at {csv_path}")
        return csv_metadata
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                letter_id = row.get('id')
                if letter_id:
                    csv_metadata[letter_id] = row
    except Exception as e:
        print(f"Error loading CSV metadata: {e}")
    
    return csv_metadata

def compute_embedding(text, tokenizer, model):
    try:
        # Get the device from the model
        if torch is None or model is None or tokenizer is None:
            raise RuntimeError("Embedding model not available")
        device = next(model.parameters()).device

        # Tokenize and move to the same device as the model
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Forward pass
        with torch.no_grad():
            outputs = model(**inputs)

        hidden = outputs.last_hidden_state  # (batch, seq_len, dim)

        # Pool according to POOLING strategy
        if POOLING == "cls":
            pooled = hidden[:, 0, :]  # first token
        elif POOLING == "mean+max":
            mean_vec = hidden.mean(dim=1)
            max_vec = hidden.max(dim=1).values
            pooled = torch.cat([mean_vec, max_vec], dim=1)  # (batch, 2*dim)
        else:  # default to mean pooling
            pooled = hidden.mean(dim=1)

        # Move result back to CPU for numpy conversion
        embedding = pooled.squeeze().cpu().numpy()
        return embedding
    except RuntimeError as e:
        error_str = str(e).lower()
        if "cuda" in error_str and ("kernel" in error_str or "compatibility" in error_str or "sm_" in error_str):
            print(f"[ERROR] CUDA compatibility issue detected: {e}")
            print("This GPU may not be supported by the current PyTorch version.")
            print("Consider using CPU mode with DARWIN_FORCE_CPU=true or upgrading PyTorch.")
        else:
            print(f"Runtime error computing embedding: {e}")
        return None
    except Exception as e:
        print(f"Error computing embedding for text: {text[:50]}... - {str(e)}")
        return None

def process_letters(letters_dir, vector_store, tokenizer, model, csv_metadata):
    """Process all letter XML files and add them to the vector store."""
    print(f"Processing letters from: {letters_dir}")
    
    text_splitter = get_text_splitter(TEXT_SPLITTER_TYPE, CHUNK_SIZE, CHUNK_OVERLAP)
    letters_dir_path = letters_dir if os.path.isabs(letters_dir) else resolve_path(letters_dir)
    
    if not os.path.exists(letters_dir_path):
        print(f"Error: Letters directory not found: {letters_dir_path}")
        return
    
    # Get all XML files
    xml_files = []
    for file in os.listdir(letters_dir_path):
        if file.endswith('.xml') and file.startswith('DCP-LETT-'):
            xml_files.append(os.path.join(letters_dir_path, file))
    
    print(f"Found {len(xml_files)} letter XML files")
    
    texts, metadatas, embeddings = [], [], []

    # Prepare BM25 corpus file (overwrite on each run)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        bm25_fh = open(BM25_CORPUS_PATH, 'w', encoding='utf-8')
    except Exception as e:
        print(f"Warning: Could not open BM25 corpus file for writing: {e}")
        bm25_fh = None
    
    def add_batch_to_store(texts_batch, metadatas_batch, embeddings_batch):
        nonlocal texts, metadatas, embeddings
        
        if not texts_batch:
            return True
        
        # Filter out any entries with None or empty values
        valid_entries = []
        for i, (text, meta, emb) in enumerate(zip(texts_batch, metadatas_batch, embeddings_batch)):
            if not text or not meta:
                continue
            # Convert any potential None values in metadata to strings
            for key in meta:
                if meta[key] is None:
                    meta[key] = "None"
            if LEXICAL_ONLY:
                # Accept even if embedding is None in lexical-only mode
                valid_entries.append((text, meta, None))
            else:
                if emb is not None:
                    valid_entries.append((text, meta, emb))
        
        if not valid_entries:
            return True
            
        # Unpack the valid entries
        texts_filtered, metadatas_filtered, embeddings_filtered = zip(*valid_entries)
        texts_filtered, metadatas_filtered, embeddings_filtered = list(texts_filtered), list(metadatas_filtered), list(embeddings_filtered)
        
        try:
            if not LEXICAL_ONLY and vector_store is not None:
                vector_store.add_texts(texts_filtered, metadatas=metadatas_filtered, embeddings=embeddings_filtered)

            # Append to BM25 corpus JSONL for hybrid retrieval
            if bm25_fh is not None:
                for txt, meta in zip(texts_filtered, metadatas_filtered):
                    uid = f"{meta.get('letter_id','unknown')}#{meta.get('chunk_index',0)}"
                    rec = {"id": uid, "text": txt, "metadata": meta}
                    try:
                        bm25_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    except Exception as e:
                        # Non-fatal write error
                        print(f"Warning: Failed to write BM25 record for {uid}: {e}")

            texts, metadatas, embeddings = [], [], []
            letter_stats['successful_batches'] += 1
            return True
        except Exception as e:
            print(f"Error adding batch to vector store: {e}")
            return False
    
    # Process each letter
    for xml_file in tqdm(xml_files, desc="Processing letters", ncols=80):
        try:
            letter_data = parse_letter_xml(xml_file)
            if not letter_data:
                letter_stats['skipped_letters'] += 1
                continue
            
            letter_stats['total_letters'] += 1
            
            # Get additional metadata from CSV if available
            csv_data = csv_metadata.get(letter_data['letter_id'], {})
            
            # Split the letter transcription into chunks
            chunks = text_splitter.split_text(letter_data['transcription'])
            
            for chunk_idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                # Skip chunks that are too short to be meaningful
                if len(chunk.strip()) < MIN_CHUNK_LEN:
                    continue
                
                # Compute embedding for this chunk (skip in lexical-only mode)
                embedding = None
                if not LEXICAL_ONLY:
                    embedding = compute_embedding(chunk, tokenizer, model)
                    if embedding is None:
                        continue
                    
                    # Validate embedding
                    if not (isinstance(embedding, np.ndarray) and not np.isnan(embedding).any() and not np.isinf(embedding).any()):
                        continue
                
                # Update statistics
                letter_stats['total_chunks'] += 1
                letter_stats['total_chars'] += len(chunk)
                letter_stats['total_words'] += len(chunk.split())
                
                # Create metadata for this chunk
                metadata_dict = {
                    "letter_id": letter_data['letter_id'] or "unknown",
                    "sender_name": letter_data['sender_name'] or "unknown",
                    "recipient_name": letter_data['recipient_name'] or "unknown",
                    "sender_place": letter_data['sender_place'],
                    "date_sent": letter_data['date_sent'],
                    "year": letter_data['year'],
                    "abstract": letter_data['abstract'],
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks),
                    "source_file": os.path.basename(letter_data['source_file']),
                    "sender_surname": csv_data.get('sender_surname'),
                    "sender_forename": csv_data.get('sender_forename'),
                    "recipient_surname": csv_data.get('recipient_surname'),
                    "recipient_forename": csv_data.get('recipient_forename'),
                    "sender_address": csv_data.get('sender_address'),
                    "recipient_address": csv_data.get('recipient_address'),
                    "source": csv_data.get('source'),
                    "corpus": "darwin",
                    # TEI enrichments converted to strings (Chroma doesn't support lists)
                    "tei_persons": "; ".join(letter_data.get('tei_persons', [])) or None,
                    "tei_places": "; ".join(letter_data.get('tei_places', [])) or None,
                    "tei_orgs": "; ".join(letter_data.get('tei_orgs', [])) or None,
                    "tei_taxa": "; ".join(letter_data.get('tei_taxa', [])) or None,
                    # Bibliography simplified to string format
                    "tei_bibl": "; ".join(letter_data.get('tei_bibl', [])) or None,
                    "tei_bibl_struct_count": len(letter_data.get('tei_bibl_struct', []))
                }
                
                texts.append(chunk)
                metadatas.append(metadata_dict)
                if LEXICAL_ONLY:
                    embeddings.append(None)
                else:
                    embeddings.append(embedding.tolist())
                
                # Process batch when we reach the batch size
                if len(texts) >= BATCH_SIZE:
                    success = add_batch_to_store(texts, metadatas, embeddings)
                    if success:
                        print(f"Added batch to vector store. Total chunks: {letter_stats['total_chunks']}")
                    
        except Exception as e:
            print(f"Error processing letter {xml_file}: {e}")
            letter_stats['skipped_letters'] += 1
    
    # Process any remaining texts
    if texts:
        add_batch_to_store(texts, metadatas, embeddings)

    # Close BM25 file handle
    try:
        if bm25_fh is not None:
            bm25_fh.close()
            print(f"BM25 corpus written to: {BM25_CORPUS_PATH}")
    except Exception:
        pass
    
    print(f"\nProcessing complete:")
    print(f"Total letters processed: {letter_stats['total_letters']}")
    print(f"Total chunks created: {letter_stats['total_chunks']}")
    print(f"Skipped letters: {letter_stats['skipped_letters']}")
    print(f"Successful batches: {letter_stats['successful_batches']}")

def generate_vector_store_stats(
    collection_name: str,
    model_name: str,
    embedding_dimension: int,
    processing_time: float,
    output_file: str
) -> None:
    """Generate comprehensive statistics about the vector store creation process."""
    try:
        # Get system information
        cpu_logical = psutil.cpu_count() if psutil else os.cpu_count()
        ram_total = f"{psutil.virtual_memory().total / (1024**3):.1f} GB" if psutil else "Unknown"
        has_torch = torch is not None and getattr(torch, 'cuda', None) is not None
        system_info = {
            "OS": platform.system(),
            "OS Version": platform.version(),
            "Python Version": platform.python_version(),
            "CPU": platform.processor(),
            "CPU Cores": f"{os.cpu_count()} physical, {cpu_logical} logical",
            "RAM": ram_total,
            "GPU": torch.cuda.get_device_name(0) if has_torch and torch.cuda.is_available() else "None",
            "CUDA Version": torch.version.cuda if has_torch and torch.cuda.is_available() else "N/A"
        }

        # Build the statistics string
        stats_lines = [
            "Darwin Corpus Vector Store Creation Statistics",
            "============================================",
            "",
            f"Collection: {collection_name}",
            f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Model Information",
            "---------------",
            f"Model: {model_name}",
            f"Embedding Dimension: {embedding_dimension}",
            f"Pooling Strategy: {POOLING}",
            "",
            "Processing Configuration",
            "----------------------",
            f"Text Splitter: {TEXT_SPLITTER_TYPE}",
            f"Chunk Size: {CHUNK_SIZE}",
            f"Chunk Overlap: {CHUNK_OVERLAP}",
            f"Batch Size: {BATCH_SIZE}",
            "",
            "Document Statistics", 
            "------------------",
            f"Total Letters Processed: {letter_stats['total_letters']:,}",
            f"Total Chunks Created: {letter_stats['total_chunks']:,}",
            f"Total Characters: {letter_stats['total_chars']:,}",
            f"Total Words: {letter_stats['total_words']:,}",
            f"Skipped Letters: {letter_stats['skipped_letters']:,}",
            f"Successful Batches: {letter_stats['successful_batches']:,}",
            "",
            "Average Statistics",
            "----------------",
            f"Average Chunks per Letter: {letter_stats['total_chunks'] / max(letter_stats['total_letters'], 1):.1f}",
            f"Average Characters per Chunk: {letter_stats['total_chars'] / max(letter_stats['total_chunks'], 1):.1f}",
            f"Average Words per Chunk: {letter_stats['total_words'] / max(letter_stats['total_chunks'], 1):.1f}",
            "",
            "Processing Statistics",
            "-------------------",
            f"Total Processing Time: {processing_time:.2f} seconds",
            f"Average Time per Letter: {processing_time / max(letter_stats['total_letters'], 1):.2f} seconds",
            f"Chunks per Second: {letter_stats['total_chunks'] / max(processing_time, 1):.1f}",
            "",
            "System Information",
            "----------------",
            f"OS: {system_info['OS']} {system_info['OS Version']}",
            f"Python: {system_info['Python Version']}",
            f"CPU: {system_info['CPU']}",
            f"CPU Cores: {system_info['CPU Cores']}",
            f"RAM: {system_info['RAM']}",
            f"GPU: {system_info['GPU']}",
            f"CUDA Version: {system_info['CUDA Version']}"
        ]

        # Join all lines with newlines and write to file
        stats = "\n".join(stats_lines)
        with open(output_file, 'w') as f:
            f.write(stats)
            
        print(f"\nStatistics written to: {output_file}")
        
    except Exception as e:
        print(f"Error generating statistics: {e}")

def verify_letter_documents(vector_store):
    """Verify that letter documents are retrievable from the vector store."""
    print("\n=== Verifying Letter Document Retrieval ===")
    
    # Test queries
    test_queries = [
        "evolution",
        "species",
        "natural selection",
        "voyage",
        "Beagle"
    ]
    
    verification_results = {}
    
    for query in test_queries:
        print(f"Testing retrieval with query: '{query}'")
        try:
            # Best-effort guard: enforce CPU verification if HF embeddings support it
            results = vector_store.similarity_search(query, k=3)
            
            if results:
                verification_results[query] = {
                    "status": "SUCCESS",
                    "count": len(results),
                    "sample_letters": [doc.metadata.get('letter_id', 'unknown') for doc in results]
                }
                print(f"  ✅ Successfully retrieved {len(results)} chunks")
            else:
                verification_results[query] = {
                    "status": "EMPTY",
                    "count": 0,
                    "error": "No documents found"
                }
                print(f"  ⚠️ No documents found for query: '{query}'")
                
        except Exception as e:
            verification_results[query] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"  ❌ Error retrieving documents for '{query}': {e}")
    
    # Write verification results to file
    verification_file = os.path.join(OUTPUT_DIR, "letter_verification.json")
    with open(verification_file, 'w') as f:
        json.dump(verification_results, f, indent=2)
    
    print(f"Verification results written to: {verification_file}")
    
    # Check if any queries failed
    failed_queries = [query for query, result in verification_results.items() 
                     if result.get("status") != "SUCCESS"]
    
    if failed_queries:
        print(f"\n⚠️ WARNING: The following queries may have issues: {', '.join(failed_queries)}")
    else:
        print("\n✅ All test queries verified successfully!")
    
    return verification_results

def check_cuda_compatibility():
    """Check CUDA compatibility and return the best device to use."""
    if torch is None or not hasattr(torch, 'cuda'):
        return "cpu", "PyTorch CUDA not available"
    
    if not torch.cuda.is_available():
        return "cpu", "CUDA not available"
    
    try:
        device_count = torch.cuda.device_count()
        if device_count == 0:
            return "cpu", "No CUDA devices found"
        
        # Get GPU info for the first device
        device_name = torch.cuda.get_device_name(0)
        compute_capability = torch.cuda.get_device_capability(0)
        
        print(f"GPU detected: {device_name} (compute capability {compute_capability})")
        
        # Check for RTX 5090 or other sm_120 devices
        if compute_capability >= (12, 0):
            return "cpu", f"GPU compute capability {compute_capability} not supported by current PyTorch (max: 9.0)"
        
        # Test actual CUDA functionality with a simple operation
        try:
            test_tensor = torch.tensor([1.0], device='cuda')
            test_result = test_tensor + test_tensor
            test_result.cpu()
            return "cuda", "CUDA compatible and functional"
        except Exception as e:
            return "cpu", f"CUDA test failed: {str(e)}"
            
    except Exception as e:
        return "cpu", f"CUDA check failed: {str(e)}"

def main():
    """Main function to create the Darwin corpus Chroma vector store."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Create Darwin corpus Chroma vector store")
    parser.add_argument("--corpus-mode", choices=["full", "test"], default="test",
                       help="Corpus mode: 'full' (~15K letters) or 'test' (~16 letters)")
    args = parser.parse_args()
    
    # Override XML directory based on corpus mode
    global LETTERS_XML_DIR
    if args.corpus_mode == "full":
        LETTERS_XML_DIR = DEFAULT_FULL_XML
        print("🔥 FULL corpus mode: Processing complete Darwin correspondence (~15,000 letters)")
    else:
        LETTERS_XML_DIR = DEFAULT_TEST_XML
        print("🧪 TEST corpus mode: Processing test subset (~16 letters)")
    
    print(f"Starting Darwin corpus Chroma vector store creation...")
    print(f"📁 Source directory: {LETTERS_XML_DIR}")
    
    # Prepare output directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chroma_dir = OUTPUT_CHROMA_DIR
    
    # Ensure Chroma directory is ready (skip in lexical-only mode)
    if not LEXICAL_ONLY:
        if not ensure_chroma_directory(chroma_dir):
            print("Failed to prepare Chroma directory. Exiting.")
            sys.exit(1)
    
    # Check for GPU availability with enhanced compatibility checking
    force_cpu = os.getenv('DARWIN_FORCE_CPU', os.getenv('FORCE_CPU', 'false')).lower() in ('1', 'true', 'yes')
    
    if force_cpu:
        device = "cpu"
        print("Using device: cpu (forced)")
    else:
        device, reason = check_cuda_compatibility()
        print(f"Using device: {device} ({reason})")
    
    if LEXICAL_ONLY:
        print("[INFO] Lexical-only mode: skipping embedding model and Chroma init")
        embeddings = None
        vector_store = None
        tokenizer = None
        model = None
    else:
        # Initialize tokenizer and model first
        print(f"Initializing embedding model: {EMBEDDING_MODEL}")
        tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
        model = AutoModel.from_pretrained(EMBEDDING_MODEL)

        # Try to move model to the chosen device, fall back to CPU on any issues
        try:
            model.to(device)
            # Enhanced CUDA probe test with actual embedding computation
            if device == "cuda":
                print("Performing CUDA embedding test...")
                _probe_text = "This is a test sentence for CUDA compatibility."
                _probe_result = compute_embedding(_probe_text, tokenizer, model)
                if _probe_result is None:
                    raise RuntimeError("CUDA embedding test failed")
                print("✅ CUDA embedding test passed")
        except Exception as e:
            if device == "cuda":
                print(f"[WARN] CUDA device test failed: {e}")
                print("Falling back to CPU for embeddings...")
                device = "cpu"
                try:
                    model.to(device)
                    print("✅ Successfully fell back to CPU")
                except Exception as cpu_e:
                    print(f"[ERROR] CPU fallback also failed: {cpu_e}")
                    sys.exit(1)
            else:
                print(f"[ERROR] Model initialization failed: {e}")
                sys.exit(1)

        # Initialize embedding function and vector store with the final device
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}
        )
        vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=chroma_dir
        )
    
    # Load CSV metadata
    csv_metadata = load_csv_metadata()
    print(f"Loaded metadata for {len(csv_metadata)} letters from CSV")
    
    # Process letters
    start_time = time.time()
    process_letters(LETTERS_XML_DIR, vector_store, tokenizer, model, csv_metadata)
    total_time = time.time() - start_time
    
    # Persist the vector store
    if not LEXICAL_ONLY and vector_store is not None:
        vector_store.persist()
        print("\nChroma vector store created and automatically persisted")
    
    # Generate statistics
    stats_file = os.path.join(OUTPUT_DIR, f"{COLLECTION_NAME}.txt")
    generate_vector_store_stats(
        collection_name=COLLECTION_NAME,
        model_name=EMBEDDING_MODEL,
        embedding_dimension=768,  # Default for BERT models
        processing_time=total_time,
        output_file=stats_file
    )
    
    # Verify letter documents unless explicitly skipped; avoid if CUDA errors forced CPU fallback mid-run
    skip_verify = os.getenv('DARWIN_SKIP_VERIFY', 'false').lower() in ('1', 'true', 'yes')
    if not skip_verify and not LEXICAL_ONLY and vector_store is not None:
        try:
            verify_letter_documents(vector_store)
        except Exception as e:
            print(f"[WARN] Skipping verification due to error: {e}")
    
    print(f"\n✅ Darwin corpus vector store creation completed successfully!")
    print(f"Processing time: {total_time:.2f} seconds")
    print(f"Processed {letter_stats['total_letters']} letters into {letter_stats['total_chunks']} chunks")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())