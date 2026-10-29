(() => {
  const messageList = document.getElementById("chat-messages");
  if (!messageList) return;
  const form = document.getElementById("chat-form");
  const input = document.getElementById("message-input");
  const typing = document.getElementById("typing-indicator");
  const suggestions = document.getElementById("suggestions");
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";
  let conversationId = null;
  let busy = false;

  const timeLabel = (value = new Date()) =>
    new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(new Date(value));

  function appendMessage(role, content, timestamp) {
    const row = document.createElement("div");
    row.className = `message-row ${role === "user" ? "message-row-user" : "message-row-bot"}`;
    const bubble = document.createElement("div");
    bubble.className = `message-bubble ${role === "user" ? "bubble-user" : "bubble-bot"}`;
    bubble.textContent = content;
    const stamp = document.createElement("time");
    stamp.className = "message-time";
    stamp.textContent = timeLabel(timestamp);
    stamp.dateTime = new Date(timestamp || Date.now()).toISOString();
    row.append(bubble, stamp);
    messageList.append(row);
    messageList.scrollTop = messageList.scrollHeight;
  }

  function showWelcome() {
    appendMessage("assistant", "Hi there! I’m IntelliBot, your customer support assistant. Ask me about products, delivery, returns, payments, or anything else I can help with.");
    renderSuggestions(["What are your delivery options?", "What is your return policy?", "How can I contact support?"]);
  }

  function renderSuggestions(items) {
    suggestions.replaceChildren();
    items.forEach((text) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "suggestion-chip";
      button.textContent = text;
      button.addEventListener("click", () => {
        input.value = text;
        form.requestSubmit();
      });
      suggestions.append(button);
    });
  }

  function setBusy(value) {
    busy = value;
    typing.classList.toggle("hidden", !value);
    input.disabled = value;
    form.querySelector("button").disabled = value;
  }

  async function loadConversation() {
    const response = await fetch("/api/conversations", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("Could not load conversations.");
    const data = await response.json();
    const latest = data.conversations[0];
    if (!latest) {
      const created = await fetch("/api/conversations", {
        method: "POST", headers: { "X-CSRFToken": csrf, Accept: "application/json" },
      });
      if (!created.ok) throw new Error("Could not start a conversation.");
      conversationId = (await created.json()).conversation.id;
      showWelcome();
      return;
    }
    conversationId = latest.id;
    const detail = await fetch(`/api/conversations/${conversationId}`, { headers: { Accept: "application/json" } });
    if (!detail.ok) throw new Error("Could not load conversation history.");
    const payload = await detail.json();
    const messages = payload.conversation.messages || [];
    messages.forEach((message) => appendMessage(message.role, message.content, message.created_at));
    if (!messages.length) showWelcome();
    else renderSuggestions(["What are your delivery options?", "What is your return policy?", "How can I contact support?"]);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || busy) return;
    appendMessage("user", message);
    input.value = "";
    renderSuggestions([]);
    setBusy(true);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf, Accept: "application/json" },
        body: JSON.stringify({ message, conversation_id: conversationId }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error?.message || "Your message couldn’t be sent.");
      conversationId = data.conversation_id;
      appendMessage("assistant", data.response, data.created_at);
      renderSuggestions(data.suggestions || []);
    } catch (error) {
      appendMessage("assistant", error.message || "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
      input.focus();
    }
  });

  document.getElementById("new-chat").addEventListener("click", async () => {
    if (busy) return;
    try {
      const response = await fetch("/api/conversations", {
        method: "POST", headers: { "X-CSRFToken": csrf, Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Could not start a new conversation.");
      conversationId = (await response.json()).conversation.id;
      messageList.replaceChildren();
      showWelcome();
      input.focus();
    } catch (error) {
      appendMessage("assistant", error.message);
    }
  });

  document.getElementById("clear-chat").addEventListener("click", async () => {
    if (busy || !conversationId || !confirm("Clear this conversation and permanently delete its messages?")) return;
    try {
      const response = await fetch(`/api/conversations/${conversationId}`, {
        method: "DELETE",
        headers: { "X-CSRFToken": csrf, Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Could not clear this conversation.");
      const created = await fetch("/api/conversations", {
        method: "POST", headers: { "X-CSRFToken": csrf, Accept: "application/json" },
      });
      if (!created.ok) throw new Error("Your conversation was cleared, but a new one could not be started.");
      conversationId = (await created.json()).conversation.id;
      messageList.replaceChildren();
      showWelcome();
      input.focus();
    } catch (error) {
      appendMessage("assistant", error.message);
    }
  });

  loadConversation().catch(() => {
    appendMessage("assistant", "I couldn’t load your conversation right now. Please refresh the page to try again.");
  });
})();
