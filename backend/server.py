from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate
from pydantic import BaseModel
from pymongo import MongoClient
import aio_pika
import asyncio
import json
import os
import numpy as np
from openai import OpenAI
import logging
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_pagination(app)
# MongoDB setup
client = MongoClient("mongodb://mongodb:27017")
db = client["azure_arch"]
queries = db["queries"]

# OpenAI setup
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# RabbitMQ queue sender
def queue_message(message: dict):
    async def send():
        connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
        channel = await connection.channel()
        queue = await channel.declare_queue("ai_tasks", durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()), routing_key=queue.name
        )
        await connection.close()

    asyncio.run(send())


class QueryRequest(BaseModel):
    question: str


def get_embedding(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small", input=text
    )
    return response.data[0].embedding


def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@app.get("/queries", response_model=Page[dict])
def get_queries():
    # Fetch all queries as a list (MongoDB cursor to list)
    items = list(
        queries.find(
            {}, {"_id": 0, "question": 1, "status": 1, "response": 1, "created_at": 1}
        )
    )
    return paginate(items)


@app.post("/query")
def ask_question(data: dict):
    question = data["question"]
    logger.info(f"POST /query called with question: {question}")
    user_vec = get_embedding(question)
    for doc in queries.find({"embedding": {"$exists": True}}):
        score = cosine_similarity(user_vec, doc["embedding"])
        if score > 0.8:
            logger.info(f"Found matching query with score {score}")
            return {
                "query_id": str(doc["_id"]),
                "status": "matched",
                "response": doc["response"],
            }

    # No match, queue for processing
    doc = {
        "question": question,
        "embedding": user_vec,
        "status": "pending",
        "response": None,
        "created_at": datetime.utcnow(),  # Save as datetime object
    }
    inserted = queries.insert_one(doc)
    logger.info(f"Inserted new query with id {inserted.inserted_id}")
    queue_message({"query_id": str(inserted.inserted_id), "question": question})
    return {"query_id": str(inserted.inserted_id), "status": "queued"}
