# Azure Architecture Q&A Platform

A full-stack web application that allows users to ask questions about Azure architecture and receive AI-powered suggestions, including reference architectures. The backend combines a custom web scraper and OpenAI's AI to provide more accurate and relevant answers. The app features a modern React frontend, a FastAPI backend, and MongoDB for data storage.

---

## 🧠 **Project Idea**

This project is designed to help users (developers, architects, students) get quick, AI-generated answers and reference architectures for Azure-related questions. When a user submits a question, the backend uses a combination of a custom scraper (to gather up-to-date information from trusted sources) and OpenAI (for intelligent suggestions), resulting in more accurate and helpful responses. Users can submit questions, view previous queries, and receive helpful links and summaries.

---

## 🚀 **Technologies Used**

- **Frontend:** React (with modern CSS)
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **AI Integration:** OpenAI API
- **Scraping:** Custom Python scraper
- **Other:** Axios, Docker (required for deployment and development)

---

---

## ⚖️ **Design Trade-Offs**

This project intentionally balances AI usage with performance and cost-efficiency:

- 🔍 **Hybrid Query Engine:** The system first attempts to match user questions to existing queries using vector embeddings in MongoDB (cheap and fast). Only if no match is found is a new OpenAI call made (more expensive).
- 🧠 **Worker-Based AI Execution:** AI processing and scraping are offloaded to a background worker using RabbitMQ. This avoids blocking the main server thread and allows for better scalability.
- 🔄 **Startup Scraping:** The scraper runs once at container startup to avoid over-scraping during dev/demo, although it's possible to later convert this into a periodic cron or event-based update.
- 📁 **Separation of Concerns:** The scraper and API server are split into different services for maintainability and future scalability.
- 💰 **Cost Awareness:** OpenAI is only used when necessary, keeping the application's cloud costs under control.

---

## 🐳 **How to Run (Docker Only)**

This project is designed to be run **exclusively with Docker Compose**. This will set up the backend, frontend, and MongoDB with a single command.

### 1. **Set up your OpenAI API key**

Before running the project, create a `.env` file in the project root with your OpenAI API key:

```
OPENAI_API_KEY=your-openai-api-key-here
```

### 2. **Start the project**

```bash
docker-compose up -d --build
```

- The frontend will be available at [http://localhost:3000](http://localhost:3000)
- The backend API will be available at [http://localhost:8000](http://localhost:8000)

**Make sure your `.env` file is present and contains your OpenAI API key before starting Docker Compose.**

---

## 📝 **One-Time Script**

If you need to run a one-time data scraping or setup script, use:

```bash
 docker-compose run --rm azure_scraper python3 backend/scrape_once.py
```

---

## 📚 **API Endpoints**

- `POST /query` — Ask a new question (expects `{ question: "..." }`)
- `GET /queries` — Get previous questions (supports pagination: `skip`, `limit`)

---

## 💡 **How it Works**

1. User submits a question via the frontend.
2. The backend receives the question, uses the custom scraper to gather relevant information, and queries OpenAI for a suggestion.
3. The backend combines the scraped data and AI-generated content to create a more accurate answer, then stores the result in MongoDB.
4. The frontend displays the AI suggestion and any reference architectures.
5. Users can browse previous questions and answers with pagination.

---

## 🛠️ **Development Notes**

- Make sure to set your OpenAI API key before running the backend (see Docker instructions).
- For production, update CORS settings and environment variables as needed.
- The frontend and backend communicate via REST API (see `frontend/src/api.js`).
