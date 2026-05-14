const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export async function sendMessage(conversationId, message) {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: conversationId,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error ${res.status}: ${err}`);
  }
  const data = await res.json();
  // Map our response format to what the UI expects
  // Build agent_name from tools used
  let agentLabel = "Clinical_ITSM_AGENT";
  if (data.tools_used && data.tools_used.length > 0) {
    agentLabel = data.tools_used.join(" → ");
  }
  return {
    conversation_id: data.session_id,
    response: data.reply,
    agent_name: agentLabel,
  };
}

export async function getConversations() {
  // Not supported in our backend — return empty
  return [];
}

export async function getConversation(conversationId) {
  // Not supported — return empty
  return { messages: [] };
}

export async function deleteConversation(conversationId) {
  const res = await fetch(`${API_URL}/api/conversations/${conversationId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete conversation");
  return res.json();
}

export async function healthCheck() {
  const res = await fetch(`${API_URL}/api/health`);
  return res.json();
}
