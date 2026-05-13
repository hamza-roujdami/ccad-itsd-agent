import React, { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import TicketFormBubble from "./TicketFormBubble";

export default function ChatWindow({
  messages,
  loading,
  conversationId,
  onSend,
  ticketComposer,
  onOpenTicketComposer,
  onCloseTicketComposer,
  onSubmitTicketComposer,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  if (!conversationId) {
    return (
      <div className="welcome-state">
        <h2 style={{ fontSize: "22px", fontWeight: 600, marginBottom: "8px" }}>
          Welcome to Agent Hub
        </h2>
        <p style={{ maxWidth: "420px", fontSize: "14px" }}>
          Your enterprise AI assistant powered by a multi-agent orchestration
          pipeline. Ask questions, create tickets, or get department contacts.
        </p>
        <div className="icon-grid">
          <div className="agent-card">
            <div className="card-emoji">📚</div>
            <div className="card-title">RAG Agent</div>
            <div className="card-desc">Knowledge base search & answers</div>
          </div>
          <div className="agent-card">
            <div className="card-emoji">🎫</div>
            <div className="card-title">Ticketing Agent</div>
            <div className="card-desc">Create & track support tickets</div>
          </div>
          <div className="agent-card">
            <div className="card-emoji">📇</div>
            <div className="card-title">Fallback Agent</div>
            <div className="card-desc">HR & Sales department contacts</div>
          </div>
        </div>
        <p style={{ fontSize: "12px", color: "var(--text-muted)" }}>
          Start a new conversation to begin →
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="chat-header">
        <span style={{ fontWeight: 600 }}>Conversation</span>
        <span className="conv-id">{conversationId}</span>
      </div>
      <div className="chat-messages">
        {messages.length === 0 && (
          <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "60px 0", fontSize: "14px" }}>
            Send a message to start the conversation.
          </div>
        )}
        {messages.map((msg, i) => {
          const isRag = msg.role === "assistant" && msg.metadata?.agent === "rag";
          // Find the preceding user message to use as ticket context
          let userQuestion = "";
          if (isRag) {
            for (let j = i - 1; j >= 0; j--) {
              if (messages[j].role === "user") {
                userQuestion = messages[j].content;
                break;
              }
            }
          }
          return (
            <MessageBubble
              key={i}
              role={msg.role}
              content={msg.content}
              agentName={msg.metadata?.agent}
              timestamp={msg.timestamp}
              onCreateTicket={
                isRag && onOpenTicketComposer
                  ? () => onOpenTicketComposer({ issueContext: userQuestion, sourceAgent: msg.metadata?.agent })
                  : undefined
              }
            />
          );
        })}
        {ticketComposer && (
          <TicketFormBubble
            issueContext={ticketComposer.issueContext}
            onCancel={onCloseTicketComposer}
            onSubmit={onSubmitTicketComposer}
            disabled={loading}
          />
        )}
        {loading && (
          <div className="message-row assistant">
            <div className="message-bubble">
              <div className="typing-indicator">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </>
  );
}
