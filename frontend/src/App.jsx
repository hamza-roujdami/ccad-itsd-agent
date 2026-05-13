import React, { useState, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import InputBar from "./components/InputBar";
import {
  sendMessage,
  getConversations,
  getConversation,
  deleteConversation,
  healthCheck,
} from "./utils/api";
import "./styles/main.css";

export default function App() {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [agentsLive, setAgentsLive] = useState(false);
  const [ticketComposer, setTicketComposer] = useState(null);

  // Health check on mount
  useEffect(() => {
    healthCheck()
      .then((data) => setAgentsLive(data.agents_live))
      .catch(() => setAgentsLive(false));
  }, []);

  // Load conversation list
  const refreshConversations = useCallback(async () => {
    try {
      const data = await getConversations();
      setConversations(data.conversations || []);
    } catch {
      // Backend may not be running yet
    }
  }, []);

  useEffect(() => {
    refreshConversations();
  }, [refreshConversations]);

  // Load messages when active conversation changes
  useEffect(() => {
    if (!activeId) {
      setMessages([]);
      setTicketComposer(null);
      return;
    }
    getConversation(activeId)
      .then((data) => setMessages(data.messages || []))
      .catch(() => setMessages([]));
  }, [activeId]);

  // Create new conversation
  const handleNewChat = () => {
    const newId = uuidv4();
    setActiveId(newId);
    setMessages([]);
    setTicketComposer(null);
    if (!conversations.includes(newId)) {
      setConversations((prev) => [newId, ...prev]);
    }
  };

  // Select existing conversation
  const handleSelect = (id) => {
    setActiveId(id);
    setTicketComposer(null);
  };

  // Delete conversation
  const handleDelete = async (id) => {
    try {
      await deleteConversation(id);
    } catch {
      // ignore
    }
    setConversations((prev) => prev.filter((c) => c !== id));
    if (activeId === id) {
      setActiveId(null);
      setMessages([]);
      setTicketComposer(null);
    }
  };

  const handleOpenTicketComposer = ({ issueContext = "", sourceAgent = "rag_agent" } = {}) => {
    setTicketComposer({
      issueContext,
      sourceAgent,
      openedAt: new Date().toISOString(),
    });
  };

  const handleCloseTicketComposer = () => {
    setTicketComposer(null);
  };

  const handleTicketComposerSubmit = async ({ issueContext, impact, urgency }) => {
    const prompt = [
      "I want to create a support ticket.",
      issueContext ? `Issue context: ${issueContext}` : "",
      `Impact: ${impact}`,
      `Urgency: ${urgency}`,
      "Use past ticket history to infer or validate category and subcategory.",
      "Verify the priority using the impact/urgency matrix, historical ticket patterns, and agent intelligence before creating the ticket.",
    ]
      .filter(Boolean)
      .join("\n");

    setTicketComposer(null);
    await handleSend(prompt);
  };

  // Send message
  const handleSend = async (text) => {
    if (!activeId || !text.trim()) return;

    const userMsg = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await sendMessage(activeId, text);
      const assistantMsg = {
        role: "assistant",
        content: data.response,
        timestamp: new Date().toISOString(),
        metadata: { agent: data.agent_name },
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Refresh conversation list in case this is a new conversation
      refreshConversations();
    } catch (err) {
      const errorMsg = {
        role: "assistant",
        content: `⚠️ Error: ${err.message}. Make sure the backend is running on http://localhost:8000`,
        timestamp: new Date().toISOString(),
        metadata: { agent: "system" },
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-layout">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={handleSelect}
        onNew={handleNewChat}
        onDelete={handleDelete}
        agentsLive={agentsLive}
      />
      <div className="chat-area">
        <ChatWindow
          messages={messages}
          loading={loading}
          conversationId={activeId}
          onSend={handleSend}
          ticketComposer={ticketComposer}
          onOpenTicketComposer={handleOpenTicketComposer}
          onCloseTicketComposer={handleCloseTicketComposer}
          onSubmitTicketComposer={handleTicketComposerSubmit}
        />
        {activeId && <InputBar onSend={handleSend} disabled={loading} />}
      </div>
    </div>
  );
}
