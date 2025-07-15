// api.js
import axios from "axios";

const API_BASE = "http://localhost:8000"; // Adjust if backend runs elsewhere

// Use 'page' and 'size' for FastAPI Pagination
export const getAllQueries = (page = 1, size = 10) =>
  axios.get(`${API_BASE}/queries`, { params: { page, size } });

export const askQuestion = (question) =>
  axios.post(`${API_BASE}/query`, { question });
