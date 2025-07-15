import React, { useState, useEffect } from "react";
import QuestionsList from "./components/QuestionsList";
import AskQuestionForm from "./components/AskQuestionForm";
import { getAllQueries } from "./api";
import "./App.css";

export default function App() {
  const [questions, setQuestions] = useState([]);

  // Fetch latest questions on load or when questions change (excluding pending ones)
  useEffect(() => {
    getAllQueries(1, 10).then((res) => {
      setQuestions((prev) => {
        // Filter out pending (unsaved) questions from prev
        const pendingQs = prev.filter((q) => q.status === "pending");
        // Remove any fetched that duplicate pending
        const fetched = res.data.items.filter(
          (q) =>
            !pendingQs.some((p) => p.question === q.question)
        );
        // Always latest first: pending + fetched
        return [...pendingQs, ...fetched];
      });
    });
  }, []);

  // Handler for optimistically adding a pending question
  const handleNewQuestion = (q) => {
    setQuestions((prev) => [{ ...q }, ...prev]);
  };

  return (
    <div className="app-container">
      <h1>Azure Architecture Q&A</h1>
      <AskQuestionForm onNewQuestion={handleNewQuestion} />
      <hr />
      <QuestionsList questions={questions} />
    </div>
  );
}
