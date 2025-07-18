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
import re, torch, json, nltk, time, subprocess, numpy as np, shutil
import platform
import psutil
from dotenv import load_dotenv
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel, AutoConfig
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
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

# Download NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except Exception as e:
    print(f"Warning: NLTK download failed: {e}")

# Data paths
LETTERS_XML_DIR = "../../../../darwin_sources_FULL/xml/letters"
LETTERS_CSV_PATH = "../../../../darwin_sources_FULL/csv/darwin-correspondence.csv"

# Helper to resolve relative paths based on this script's directory
def resolve_path(relative_path):
    script_dir = Path(__file__).resolve().parent
    return str((script_dir / relative_path).resolve())

def get_target_config():
    """Get configuration from the target file."""
    try:
        # First get the collection name from environment
        collection_name = os.getenv('CHROMA_COLLECTION_NAME', 'darwin')
        
        target_file = os.path.join('backend', 'targets', f'{collection_name}.txt')
        if not os.path.exists(target_file):
            print(f"Warning: Target file {target_file} not found, using defaults")
            return {
                'COLLECTION_NAME': collection_name,
                'CHUNK_SIZE': 1500,
                'CHUNK_OVERLAP': 250,
                'TEXT_SPLITTER_TYPE': 'RecursiveCharacterTextSplitter'
            }
            
        with open(target_file, 'r') as f:
            content = f.read()
            
        # Extract configuration values
        chunk_size = re.search(r'CHUNK_SIZE\s*=\s*(\d+)', content)
        chunk_overlap = re.search(r'CHUNK_OVERLAP\s*=\s*(\d+)', content)
        text_splitter = re.search(r'Text Splitter:\s*(\w+)', content)
        
        if not all([chunk_size, chunk_overlap, text_splitter]):
            print("Warning: Could not find all configuration in target file, using defaults")
            return {
                'COLLECTION_NAME': collection_name,
                'CHUNK_SIZE': 1500,
                'CHUNK_OVERLAP': 250,
                'TEXT_SPLITTER_TYPE': 'RecursiveCharacterTextSplitter'
            }
            
        return {
            'COLLECTION_NAME': collection_name,
            'CHUNK_SIZE': int(chunk_size.group(1)),
            'CHUNK_OVERLAP': int(chunk_overlap.group(1)),
            'TEXT_SPLITTER_TYPE': text_splitter.group(1)
        }
    except Exception as e:
        print(f"Warning: Error reading target configuration: {e}, using defaults")
        return {
            'COLLECTION_NAME': os.getenv('CHROMA_COLLECTION_NAME', 'darwin'),
            'CHUNK_SIZE': 1000,
            'CHUNK_OVERLAP': 200,
            'TEXT_SPLITTER_TYPE': 'RecursiveCharacterTextSplitter'
        }

# Get configuration
target_config = get_target_config()
COLLECTION_NAME = target_config['COLLECTION_NAME']
CHUNK_SIZE = target_config['CHUNK_SIZE']
CHUNK_OVERLAP = target_config['CHUNK_OVERLAP']
TEXT_SPLITTER_TYPE = target_config['TEXT_SPLITTER_TYPE']

# Other environment variables
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'Livingwithmachines/bert_1760_1900')
POOLING = os.getenv('POOLING', 'mean').lower()
BATCH_SIZE = 100

# Define output directories
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
OUTPUT_CHROMA_DIR = os.path.join(OUTPUT_DIR, "chroma_db")

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

def get_text_splitter(splitter_type, chunk_size, chunk_overlap):
    if splitter_type == 'RecursiveCharacterTextSplitter':
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
    elif splitter_type == 'CharacterTextSplitter':
        return CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    else:
        raise ValueError(f"Unsupported text splitter type: {splitter_type}")

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
            'source_file': xml_file_path
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
    except Exception as e:
        print(f"Error computing embedding for text: {text[:50]}... - {str(e)}")
        return None

def process_letters(letters_dir, vector_store, tokenizer, model, csv_metadata):
    """Process all letter XML files and add them to the vector store."""
    print(f"Processing letters from: {letters_dir}")
    
    text_splitter = get_text_splitter(TEXT_SPLITTER_TYPE, CHUNK_SIZE, CHUNK_OVERLAP)
    letters_dir_path = resolve_path(letters_dir)
    
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
    
    def add_batch_to_store(texts_batch, metadatas_batch, embeddings_batch):
        nonlocal texts, metadatas, embeddings
        
        if not texts_batch:
            return True
        
        # Filter out any entries with None or empty values
        valid_entries = []
        for i, (text, meta, emb) in enumerate(zip(texts_batch, metadatas_batch, embeddings_batch)):
            if text and meta and emb is not None:
                # Convert any potential None values in metadata to strings
                for key in meta:
                    if meta[key] is None:
                        meta[key] = "None"
                valid_entries.append((text, meta, emb))
        
        if not valid_entries:
            return True
            
        # Unpack the valid entries
        texts_filtered, metadatas_filtered, embeddings_filtered = zip(*valid_entries)
        texts_filtered, metadatas_filtered, embeddings_filtered = list(texts_filtered), list(metadatas_filtered), list(embeddings_filtered)
        
        try:
            vector_store.add_texts(texts_filtered, metadatas=metadatas_filtered, embeddings=embeddings_filtered)
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
                if len(chunk.strip()) < 50:
                    continue
                
                # Compute embedding for this chunk
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
                    "corpus": "darwin"
                }
                
                texts.append(chunk)
                metadatas.append(metadata_dict)
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
        system_info = {
            "OS": platform.system(),
            "OS Version": platform.version(),
            "Python Version": platform.python_version(),
            "CPU": platform.processor(),
            "CPU Cores": f"{os.cpu_count()} physical, {psutil.cpu_count()} logical",
            "RAM": f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
            "GPU": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None",
            "CUDA Version": torch.version.cuda if torch.cuda.is_available() else "N/A"
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

def main():
    """Main function to create the Darwin corpus Chroma vector store."""
    print("Starting Darwin corpus Chroma vector store creation...")
    
    # Prepare output directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chroma_dir = OUTPUT_CHROMA_DIR
    
    # Ensure Chroma directory is ready
    if not ensure_chroma_directory(chroma_dir):
        print("Failed to prepare Chroma directory. Exiting.")
        sys.exit(1)
    
    # Check for GPU availability
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Initialize the embedding model
    print(f"Initializing embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': device},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Initialize the vector store
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=chroma_dir
    )
    
    # Initialize tokenizer and model for embedding computation
    tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
    model = AutoModel.from_pretrained(EMBEDDING_MODEL)
    model.to(device)
    
    # Load CSV metadata
    csv_metadata = load_csv_metadata()
    print(f"Loaded metadata for {len(csv_metadata)} letters from CSV")
    
    # Process letters
    start_time = time.time()
    process_letters(LETTERS_XML_DIR, vector_store, tokenizer, model, csv_metadata)
    total_time = time.time() - start_time
    
    # Persist the vector store
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
    
    # Verify letter documents
    verify_letter_documents(vector_store)
    
    print(f"\n✅ Darwin corpus vector store creation completed successfully!")
    print(f"Processing time: {total_time:.2f} seconds")
    print(f"Processed {letter_stats['total_letters']} letters into {letter_stats['total_chunks']} chunks")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())