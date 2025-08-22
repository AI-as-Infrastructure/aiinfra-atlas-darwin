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
import shutil
from pathlib import Path
from datetime import datetime

def parse_manifest_file(manifest_path):
    """Parse the Darwin vector store manifest to extract configuration."""
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
            pooling_match = re.search(r'Pooling Strategy:\s*(.+)', content)
            
            if collection_match: config['COLLECTION_NAME'] = collection_match.group(1).strip()
            if model_match: config['EMBEDDING_MODEL'] = model_match.group(1).strip()
            if chunk_size_match: config['CHUNK_SIZE'] = chunk_size_match.group(1)
            if chunk_overlap_match: config['CHUNK_OVERLAP'] = chunk_overlap_match.group(1)
            if created_match: config['CREATED'] = created_match.group(1).strip()
            if text_splitter_match: config['TEXT_SPLITTER'] = text_splitter_match.group(1).strip()
            if pooling_match: config['POOLING'] = pooling_match.group(1).strip()
            
    except FileNotFoundError:
        print(f"Error: Manifest file {manifest_path} not found!")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading manifest: {e}")
        sys.exit(1)
    
    # Validate required fields
    required = ['COLLECTION_NAME', 'EMBEDDING_MODEL', 'CHUNK_SIZE', 'CHUNK_OVERLAP']
    for k in required:
        if k not in config:
            print(f"Missing {k} in manifest!")
            sys.exit(1)
    return config

def generate_enhanced_retriever(config, source_retriever_path, output_path):
    """Generate enhanced Darwin retriever by updating the working template."""
    print(f"📖 Reading source retriever from: {source_retriever_path}")
    
    # Read the current working retriever
    with open(source_retriever_path, 'r') as f:
        retriever_code = f.read()
    
    # Update the configuration values from manifest
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Add generation header
    header = f'''#!/usr/bin/env python3
"""
Auto-generated Enhanced Darwin Retriever for ATLAS
Generated: {now}
Manifest creation: {config.get('CREATED', 'Unknown')}

This retriever includes:
- Hybrid search (dense embeddings + BM25 lexical search + RRF fusion)
- Rich Darwin citation formatting with TEI entities  
- CUDA fallback for GPU compatibility
- Darwin Correspondence Project canonical URLs
- Scholarly truncation notices
- Time period and direction filtering
"""
'''
    
    # Replace the original header with generation info
    # Find the end of the existing docstring
    docstring_end = retriever_code.find('"""', retriever_code.find('"""') + 3) + 3
    if docstring_end > 2:
        retriever_code = header + retriever_code[docstring_end:]
    else:
        retriever_code = header + retriever_code
    
    # Update configuration placeholders if they exist in template format
    replacements = {
        '"{COLLECTION_NAME}"': f'"{config["COLLECTION_NAME"]}"',
        '"{EMBEDDING_MODEL}"': f'"{config["EMBEDDING_MODEL"]}"', 
        '"{CHUNK_SIZE}"': f'"{config["CHUNK_SIZE"]}"',
        '"{CHUNK_OVERLAP}"': f'"{config["CHUNK_OVERLAP"]}"',
    }
    
    for placeholder, value in replacements.items():
        if placeholder in retriever_code:
            retriever_code = retriever_code.replace(placeholder, value)
    
    # Ensure proper environment variable usage for persist directory
    if 'persist_directory = ' in retriever_code and 'os.getenv' not in retriever_code:
        retriever_code = retriever_code.replace(
            'persist_directory = "backend/targets/chroma_db"',
            'persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "backend/targets/chroma_db")'
        )
    
    print(f"📝 Writing enhanced retriever to: {output_path}")
    
    # Write the enhanced retriever
    with open(output_path, 'w') as f:
        f.write(retriever_code)
    
    # Make executable
    os.chmod(output_path, 0o755)
    print(f"✅ Enhanced Darwin retriever generated successfully!")
    print(f"💡 Configuration: {config['EMBEDDING_MODEL']}, {config['CHUNK_SIZE']}/{config['CHUNK_OVERLAP']} chunks")

def main():
    print("🔨 Enhanced Darwin Retriever Generator")
    
    # Paths
    repo_root = Path(__file__).resolve().parents[3]
    manifest_path = repo_root / "backend/targets/darwin.txt"
    source_retriever = repo_root / "backend/retrievers/darwin_retriever.py"
    output_path = repo_root / "create/Darwin/xml/output/darwin_retriever.py"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Parse manifest
    print(f"📖 Reading manifest: {manifest_path}")
    config = parse_manifest_file(manifest_path)
    
    # Check if source retriever exists
    if not source_retriever.exists():
        print(f"❌ Error: Source retriever not found at {source_retriever}")
        sys.exit(1)
    
    # Generate enhanced retriever
    generate_enhanced_retriever(config, source_retriever, output_path)
    
    print(f"🎉 Enhanced Darwin retriever ready!")
    print(f"📁 Location: {output_path}")
    print(f"🚀 Use this retriever with ATLAS for full hybrid search capabilities")

if __name__ == "__main__":
    main()