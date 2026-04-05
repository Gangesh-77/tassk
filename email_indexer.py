from motor.motor_asyncio import AsyncIOMotorClient
from sentence_transformers import SentenceTransformer
import asyncio
import datetime
import random
from sample_emails import SAMPLE_EMAILS

# Global Configuration
MONGODB_URI = "mongodb+srv://gangeshathi_db_user:uFh2h42dIaYiVena@cluster0.jjygfov.mongodb.net/?appName=Cluster0"
DB_NAME = "email_search_db"
COLLECTION_NAME = "emails"

class EmailIndexer:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGODB_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]
        print("Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded.")

    async def generate_more_emails(self, count=45):
        categories = ["Work", "Personal", "Finance", "Travel", "Shopping", "Social", "Newsletters"]
        senders = ["boss@corp.com", "mom@gmail.com", "bank@chase.com", "support@netflix.com", "promo@uber.com", "notifications@github.com"]
        
        extra_emails = []
        for i in range(6, 6 + count):
            cat = random.choice(categories)
            sender = random.choice(senders)
            date = (datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))).isoformat()
            
            email = {
                "id": str(i),
                "sender": sender,
                "recipient": "user@gmail.com",
                "subject": f"Sample {cat} Email {i}",
                "body": f"This is an automatically generated email about {cat.lower()} stuff. We hope this content is relevant to your search demo.",
                "date": date,
                "category": cat,
                "is_read": random.choice([True, False]),
                "has_attachment": random.choice([True, False]),
                "thread_id": f"thread_{i//3}"
            }
            extra_emails.append(email)
        return extra_emails

    async def run(self):
        print("Clearing existing collection...")
        await self.collection.delete_many({})
        
        all_emails = SAMPLE_EMAILS + await self.generate_more_emails()
        
        print(f"Indexing {len(all_emails)} emails...")
        for email in all_emails:
            # Combine subject and body for better semantic search
            text_to_embed = f"{email['subject']} {email['body']}"
            vector = self.model.encode(text_to_embed).tolist()
            
            email['embedding'] = vector
            await self.collection.insert_one(email)
            
        print("Indexing completed!")

if __name__ == "__main__":
    indexer = EmailIndexer()
    asyncio.run(indexer.run())
