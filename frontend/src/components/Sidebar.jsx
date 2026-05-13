import React from "react";

export default function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  agentsLive,
}) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>
          CCAD ITSM Agent
        </h1>
        <div className="subtitle">IT Service Desk — AI-powered</div>
        <button className="new-chat-btn" onClick={onNew}>
          + New Conversation
        </button>
      </div>

      <div className="sidebar-conversations">
        {conversations.length === 0 && (
          <div style={{ padding: "16px", color: "var(--text-muted)", fontSize: "12px" }}>
            No conversations yet. Start a new one!
          </div>
        )}
        {conversations.map((id) => (
          <div
            key={id}
            className={`conv-item ${id === activeId ? "active" : ""}`}
            onClick={() => onSelect(id)}
          >
            <span className="conv-label" title={id}>
              💬 {id.slice(0, 8)}...
            </span>
            <button
              className="conv-delete"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(id);
              }}
              title="Delete conversation"
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <span className={`status-dot ${agentsLive ? "live" : "offline"}`} />
        {agentsLive ? "Agents connected" : "Simulated mode"}
      </div>
    </div>
  );
}
