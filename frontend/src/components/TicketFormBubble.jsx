import React, { useState } from "react";

const impactOptions = [
  { value: "critical", label: "Critical impact" },
  { value: "high", label: "High impact" },
  { value: "medium", label: "Medium impact" },
  { value: "low", label: "Low impact" },
];

const urgencyOptions = [
  { value: "immediate", label: "Immediate" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

export default function TicketFormBubble({ issueContext, onCancel, onSubmit, disabled }) {
  const [impact, setImpact] = useState("medium");
  const [urgency, setUrgency] = useState("medium");

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit({
      issueContext,
      impact,
      urgency,
    });
  };

  return (
    <div className="message-row assistant">
      <div className="message-bubble ticket-form-bubble">
        <form onSubmit={handleSubmit}>
          <div className="ticket-form-header">
            <div>
              <h4>Ticket intake</h4>
              <p className="ticket-form-subtitle">
                Select impact and urgency. Priority verification stays in the existing backend logic.
              </p>
            </div>
          </div>

          {issueContext && (
            <div className="ticket-form-context">
              <strong>Issue context</strong>
              <br />
              {issueContext}
            </div>
          )}

          <div className="ticket-form-grid">
            <div className="ticket-form-field">
              <label htmlFor="ticket-impact">Impact</label>
              <select
                id="ticket-impact"
                value={impact}
                onChange={(event) => setImpact(event.target.value)}
                disabled={disabled}
              >
                {impactOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="ticket-form-field">
              <label htmlFor="ticket-urgency">Urgency</label>
              <select
                id="ticket-urgency"
                value={urgency}
                onChange={(event) => setUrgency(event.target.value)}
                disabled={disabled}
              >
                {urgencyOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="ticket-form-actions">
            <button type="button" className="ticket-form-cancel" onClick={onCancel} disabled={disabled}>
              Cancel
            </button>
            <button type="submit" className="ticket-form-submit" disabled={disabled}>
              Continue in chat
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}