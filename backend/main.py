from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/vector-store-info")
async def get_vector_store_info():
    try:
        # Get the absolute path to the backend directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Use CHROMA_COLLECTION_NAME to determine the manifest file
        collection_name = os.getenv("CHROMA_COLLECTION_NAME", "darwin")
        file_path = os.path.join(current_dir, "targets", f"{collection_name}.txt")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Vector store information file not found: {collection_name}.txt")
        
        with open(file_path, "r") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 