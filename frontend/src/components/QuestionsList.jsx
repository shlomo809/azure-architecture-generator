import React, { useEffect, useState } from "react";
import { getAllQueries } from "../api";

const MAX_CHARS = 400;

export default function QuestionsList() {
  const [queries, setQueries] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState({});

  useEffect(() => {
    setLoading(true);
    getAllQueries(page, pageSize)
      .then((res) => {
        setQueries(res.data.items);
        setTotal(res.data.total);
      })
      .finally(() => setLoading(false));
  }, [page]);

  const totalPages = Math.ceil(total / pageSize);

  function getShortText(text) {
    if (text.length <= MAX_CHARS) return text;
    return text.slice(0, MAX_CHARS) + "...";
  }

  return (
    <div className="questions-list" style={{ maxWidth: 800, margin: "auto" }}>
      <h2>Previous Questions</h2>
      {loading ? (
        <div>Loading...</div>
      ) : queries.length === 0 ? (
        <div>No questions found.</div>
      ) : (
        <ul>
          {[...queries].reverse().map((q, idx) => {
            // Parse ai_suggestion and ref architectures if available
            let aiText = "";
            let refArchitectures = [];
            if (
              typeof q.response === "object" &&
              q.response !== null &&
              q.response.ai_suggestion
            ) {
              aiText = q.response.ai_suggestion.replace(/\\n/g, "\n");
              refArchitectures = q.response.reference_architectures || [];
            } else if (typeof q.response === "string") {
              aiText = q.response.replace(/\\n/g, "\n");
            }

            const isLong = aiText.length > MAX_CHARS;
            const isExpanded = expanded[idx];

            return (
              <li
                key={idx}
                style={{
                  background: "#fff",
                  marginBottom: 18,
                  padding: 18,
                  borderRadius: 8,
                  boxShadow: "0 2px 6px #0001",
                  listStyle: "none",
                }}
              >
                <div style={{ fontWeight: "bold", fontSize: 17 }}>
                  Q: {q.question}
                </div>
                <div style={{ fontSize: 13, color: "#888", margin: "2px 0 6px 0" }}>
                  {q.created_at ? new Date(q.created_at).toLocaleString() : ""}
                </div>
                <div style={{ fontSize: 14, color: "#444", margin: "4px 0" }}>
                  <b>Status:</b> {q.status}
                </div>
                <div style={{ marginTop: 8 }}>
                  <b>Response:</b>
                  <div style={{ marginTop: 6, whiteSpace: "pre-line" }}>
                    {isLong && !isExpanded
                      ? getShortText(aiText)
                      : aiText}
                    {isLong && (
                      <button
                        style={{
                          marginLeft: 8,
                          border: "none",
                          background: "none",
                          color: "#0078d4",
                          cursor: "pointer",
                          fontWeight: "bold",
                        }}
                        onClick={() =>
                          setExpanded((prev) => ({
                            ...prev,
                            [idx]: !prev[idx],
                          }))
                        }
                      >
                        {isExpanded ? "Show less" : "Show more"}
                      </button>
                    )}
                  </div>
                  {/* Only show links if expanded OR if the text isn't long */}
                  {(isExpanded || !isLong) &&
                    refArchitectures.length > 0 && (
                      <div style={{ marginTop: 8 }}>
                        <b>Reference Architectures:</b>
                        <ul>
                          {refArchitectures.map((arch, i) => (
                            <li key={i} style={{ marginBottom: 4 }}>
                              <a
                                href={arch.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ color: "#0078d4" }}
                              >
                                {arch.title}
                              </a>
                              {arch.summary && (
                                <>
                                  <br />
                                  <span style={{ fontSize: "0.95em" }}>
                                    {arch.summary}
                                  </span>
                                </>
                              )}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
      <div className="pagination" style={{ margin: "18px 0" }}>
        <button onClick={() => setPage(1)} disabled={page === 1}>
          First
        </button>
        <button onClick={() => setPage(page - 1)} disabled={page === 1}>
          Previous
        </button>
        <span>
          {" "}
          Page {page} of {totalPages}{" "}
        </span>
        <button onClick={() => setPage(page + 1)} disabled={page === totalPages}>
          Next
        </button>
        <button onClick={() => setPage(totalPages)} disabled={page === totalPages}>
          Last
        </button>
      </div>
    </div>
  );
}
