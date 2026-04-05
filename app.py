from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from sentence_transformers import SentenceTransformer
import numpy as np
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="AI Email Search API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Configuration
MONGODB_URI = "mongodb+srv://gangeshathi_db_user:uFh2h42dIaYiVena@cluster0.jjygfov.mongodb.net/?appName=Cluster0"
DB_NAME = "email_search_db"
COLLECTION_NAME = "emails"

class SearchQuery(BaseModel):
    query: str
    category: Optional[str] = None
    is_read: Optional[bool] = None
    limit: int = 10

class Email(BaseModel):
    id: str
    sender: str
    recipient: str
    subject: str
    body: str
    date: str
    category: str
    is_read: bool
    has_attachment: bool
    relevance_score: Optional[float] = None

# Initialize resources
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
model = SentenceTransformer('all-MiniLM-L6-v2')

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

@app.post("/api/search", response_model=List[Email])
async def search_emails(search_query: SearchQuery):
    # 1. Embed user query
    query_vector = model.encode(search_query.query).tolist()
    
    # 2. Build metadata filter
    mongo_filter = {}
    if search_query.category:
        mongo_filter["category"] = search_query.category
    if search_query.is_read is not None:
        mongo_filter["is_read"] = search_query.is_read
    
    # 3. Fetch candidates from MongoDB
    cursor = collection.find(mongo_filter)
    candidates = await cursor.to_list(length=100)
    
    if not candidates:
        return []
    
    # 4. Rank candidates by semantic similarity in Python
    results = []
    for doc in candidates:
        score = float(cosine_similarity(query_vector, doc['embedding']))
        doc['relevance_score'] = score
        # Remove embedding from output
        doc.pop('embedding', None)
        # Handle _id to id conversion
        doc['id'] = str(doc.get('id', ''))
        results.append(Email(**doc))
    
    # Sort by relevance score
    results.sort(key=lambda x: x.relevance_score, reverse=True)
    
    return results[:search_query.limit]

@app.get("/api/emails", response_model=List[Email])
async def get_emails(limit: int = 20, skip: int = 0):
    cursor = collection.find().sort("date", -1).skip(skip).limit(limit)
    emails = await cursor.to_list(length=limit)
    for email in emails:
        email.pop('embedding', None)
        email['id'] = str(email.get('id', ''))
    return [Email(**e) for e in emails]

@app.get("/api/stats")
async def get_stats():
    total_emails = await collection.count_documents({})
    unread_emails = await collection.count_documents({"is_read": False})
    # Simple aggregation for categories
    pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}]
    category_cursor = collection.aggregate(pipeline)
    categories = await category_cursor.to_list(length=20)
    
    return {
        "total": total_emails,
        "unread": unread_emails,
        "categories": {c["_id"]: c["count"] for c in categories}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
