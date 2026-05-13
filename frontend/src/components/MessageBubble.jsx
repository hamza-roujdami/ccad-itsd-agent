import React from "react";
import ReactMarkdown from "react-markdown";

const agentLabels = {
  rag_agent: "RAG Agent",
  ticketing_agent: "Ticketing Agent",
  fallback_agent: "Fallback Agent",
  orchestrator_agent: "Orchestrator",
};

export default function MessageBubble({ role, content, agentName, timestamp, onCreateTicket }) {
  const isUser = role === "user";
  const label = agentLabels[agentName] || agentName || "";
  const showTicketPrompt = !isUser && (agentName === "rag_agent" || agentName === "rag");

  return (
    <div className={`message-row ${isUser ? "user" : "assistant"}`}>
      <div className="message-bubble">
        {!isUser && agentName && (
          <div className={`agent-badge ${agentName}`}>{label}</div>
        )}
        <div className="message-content">
          {isUser ? (
            <p>{content}</p>
          ) : (
            <ReactMarkdown>{content}</ReactMarkdown>
          )}
        </div>
        {timestamp && (
          <div className="message-time">
            {new Date(timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>
        )}
        {showTicketPrompt && onCreateTicket && (
          <div className="ticket-prompt">
            <span>If this doesn't help, would you like to create a ticket?</span>
            <button className="ticket-prompt-btn" onClick={onCreateTicket}>
              Yes, create a ticket
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
