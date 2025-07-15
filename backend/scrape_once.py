import os
import re
import requests
from datetime import datetime
from time import sleep
from urllib.parse import urljoin
from pymongo import MongoClient
from openai import OpenAI
import logging

# MongoDB setup
client = MongoClient("mongodb://mongodb:27017")
db = client["azure_arch"]
collection = db["architectures"]

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


def estimate_complexity(services):
    count = len(services)
    if count <= 2:
        return "low"
    elif count <= 5:
        return "medium"
    else:
        return "high"


def extract_category_from_url(url):
    match = re.search(r"/architecture/(.+?)/", url)
    return match.group(1).split("/")[0] if match else "general"


def fetch_all_architectures():
    logger.info("Fetching all Azure architectures from Microsoft Docs API...")
    all_results = []
    next_url = (
        API_URL
        + "?locale=en-us&facet=products&facet=azure_categories&$orderBy=last_modified desc&$top=30&fuzzySearch=false"
    )
    while next_url:
        res = requests.get(next_url)
        res.raise_for_status()
        data = res.json()
        all_results.extend(data.get("results", []))
        next_link = data.get("@nextLink")
        if next_link:
            next_url = urljoin(BASE_URL, next_link)
            logger.debug(f"Next URL: {next_url}")
        else:
            next_url = None

    logger.info(f"Fetched {len(all_results)} architectures.")
    return all_results


def scrape_and_store():
    logger.info("Starting scrape_and_store process...")
    results = fetch_all_architectures()
    for item in results:
        title = item["title"]
        url = urljoin(BASE_URL, item["url"])
        summary = item.get("summary", "")
        thumbnail = urljoin(BASE_URL, item.get("thumbnail_url", ""))
        services = item.get("display_products", [])
        categories = item.get("display_azure_categories", [])
        tags = item.get("tags", []) + categories
        complexity = estimate_complexity(services)
        keywords = re.findall(r"\b\w+\b", title + " " + summary)
        data = {
            "title": title,
            "url": url,
            "summary": summary,
            "thumbnail_url": thumbnail,
            "azure_services": services,
            "categories": categories,
            "tags": tags,
            "category_slug": extract_category_from_url(url),
            "architecture_type": "Application" if "apps" in url else "General",
            "industries": ["General"],
            "complexity": complexity,
            "compliance": ["None"],
            "cost_tier": "moderate",
            "keywords": keywords,
            "search_tags": item.get("search_tags", []),
            "source_type": "microsoft-official",
            "scraped_at": datetime.utcnow().isoformat(),
        }
        try:
            response = openai_client.embeddings.create(
                model="text-embedding-3-small", input=f"{title}. {summary}"
            )
            data["embedding"] = response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding error for '{title}': {e}")
            continue
        collection.update_one({"url": url}, {"$set": data}, upsert=True)
        logger.debug(f"Stored/updated architecture: {title}")
        sleep(1)
    logger.info("scrape_and_store process completed.")


if __name__ == "__main__":
    scrape_and_store()
