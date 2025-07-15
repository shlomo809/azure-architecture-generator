import asyncio
import aio_pika
import json
from pymongo import MongoClient
from bson import ObjectId
from openai import OpenAI
import os
import numpy as np
import logging

# MongoDB setup
client = MongoClient("mongodb://mongodb:27017")
db = client["azure_arch"]
collection = db["architectures"]
queries = db["queries"]

# OpenAI setup
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_URL = "https://learn.microsoft.com"
API_URL = f"{BASE_URL}/api/contentbrowser/search/architectures"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def connect_rabbitmq_with_retry(max_retries=10, delay=5):
    for i in range(max_retries):
        try:
            connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
            return connection
        except Exception as e:
            print(
                f"RabbitMQ not ready, retrying in {delay}s... ({i + 1}/{max_retries})"
            )
            await asyncio.sleep(delay)
    raise ConnectionError("Failed to connect to RabbitMQ after retries")


def get_embedding(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small", input=text
    )
    return response.data[0].embedding


def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


def find_similar_architectures(user_input, limit=5):
    user_vec = get_embedding(user_input)
    results = []
    for doc in collection.find({"embedding": {"$exists": True}}):
        score = cosine_similarity(user_vec, doc["embedding"])
        results.append((score, doc))
    # Sort by similarity score, descending
    results.sort(reverse=True, key=lambda x: x[0])
    # Return the top N results
    return [doc for score, doc in results[:limit]]


def query_architecture(user_input):
    logger.info(f"Querying architecture for user input: {user_input}")
    related = find_similar_architectures(user_input, limit=5)
    examples = (
        "\n".join([f"{a['title']}: {a['summary']}" for a in related])
        or "No relevant architectures found."
    )
    logger.info(f"Examples: {examples}")
    # Prepare reference architectures with links
    reference_architectures = [
        {"title": a["title"], "summary": a["summary"], "url": a["url"]} for a in related
    ]
    logger.info(f"Reference architectures: {reference_architectures}")
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a cloud architecture assistant.",
                },
                {
                    "role": "user",
                    "content": f"Here are some reference Azure architectures:\n{examples}\n\nNow suggest one for: {user_input}",
                },
            ],
            temperature=0.5,
            max_tokens=600,
        )
        logger.info("OpenAI completion successful.")
        return {
            "ai_suggestion": response.choices[0].message.content,
            "reference_architectures": reference_architectures,
        }
    except Exception as e:
        logger.error(f"OpenAI completion error: {e}")
        return {
            "ai_suggestion": "Sorry, there was an error generating a response.",
            "reference_architectures": reference_architectures,
        }


async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        query_id = data["query_id"]
        question = data["question"]

        logger.info(f"Received message for query_id: {query_id}")
        try:
            result = query_architecture(question)
            queries.update_one(
                {"_id": ObjectId(query_id)},
                {"$set": {"status": "complete", "response": result}},
            )
            logger.info(f"Query {query_id} processed and updated in DB.")
        except Exception as e:
            logger.error(f"Error handling message for query_id {query_id}: {e}")


async def main():
    logger.info("Starting worker and connecting to RabbitMQ...")
    connection = await connect_rabbitmq_with_retry()
    channel = await connection.channel()
    queue = await channel.declare_queue("ai_tasks", durable=True)
    await queue.consume(handle_message)
    logger.info("Worker started, waiting for messages...")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
