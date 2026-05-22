import React, { useState, useRef } from "react";

export default function InputBar({ onSend, disabled }) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "46px";
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = (e) => {
    setText(e.target.value);
    // Auto-resize
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "46px";
      ta.style.height = Math.min(ta.scrollHeight, 120) + "px";
    }
  };

  return (
    <div className="input-bar">
      <form onSubmit={handleSubmit}>
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question, create a ticket, or request contacts..."
          rows={1}
          disabled={disabled}
        />
        <button type="submit" className="send-btn" disabled={disabled || !text.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
