import React, { useState } from "react";
import { askQuestion } from "../api";

export default function AskQuestionForm({ onNewQuestion }) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;

    // Optimistically show the question as pending in the list immediately
    if (onNewQuestion) {
      onNewQuestion({
        question: trimmed,
        status: "pending",
        response: "",
        createdAt: new Date().toISOString(),
        pending: true,
      });
    }

    setLoading(true);
    setQuestion(""); // Clear input immediately for good UX

    try {
      const res = await askQuestion(trimmed);
      // Optionally, you could update the question in the list here by using a unique ID or question text,
      // but for now, let the polling/refetch in QuestionsList handle updates.
    } catch (err) {
      // Optionally, show error or remove the pending question.
      alert("Failed to ask question.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Ask a New Question</h2>
      <form className="ask-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type your question..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? "Asking..." : "Ask"}
        </button>
      </form>
    </div>
  );
}
