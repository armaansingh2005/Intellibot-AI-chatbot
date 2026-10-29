(() => {
  const list = document.getElementById("history-list");
  if (!list) return;
  const count = document.getElementById("history-count");
  const detail = document.getElementById("history-detail");
  const params = new URLSearchParams(location.search);

  function dateLabel(value) {
    return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
  }

  async function openConversation(id) {
    detail.className = "history-detail";
    detail.replaceChildren();
    const response = await fetch(`/api/conversations/${encodeURIComponent(id)}`, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("This conversation could not be opened.");
    const { conversation } = await response.json();
    const heading = document.createElement("div");
    heading.className = "detail-heading";
    const title = document.createElement("h2");
    title.textContent = `Conversation #${conversation.id}`;
    const remove = document.createElement("button");
    remove.className = "text-button danger-text";
    remove.type = "button";
    remove.textContent = "Delete";
    remove.addEventListener("click", async () => {
      if (!confirm("Delete this conversation and its messages?")) return;
      const deleted = await fetch(`/api/conversations/${conversation.id}`, {
        method: "DELETE", headers: { "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content },
      });
      if (!deleted.ok) throw new Error("Could not delete this conversation.");
      location.href = "/history";
    });
    heading.append(title, remove);
    detail.append(heading);
    const transcript = document.createElement("div");
    transcript.className = "history-transcript";
    conversation.messages.forEach((message) => {
      const item = document.createElement("article");
      item.className = `history-message ${message.role === "user" ? "history-user" : "history-assistant"}`;
      const bubble = document.createElement("p");
      bubble.textContent = message.content;
      const time = document.createElement("time");
      time.textContent = dateLabel(message.created_at);
      item.append(bubble, time);
      transcript.append(item);
    });
    detail.append(transcript);
    history.replaceState(null, "", `/history?conversation=${conversation.id}`);
  }

  async function load() {
    const response = await fetch("/api/conversations", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("Could not load your conversations.");
    const data = await response.json();
    count.textContent = String(data.conversations.length);
    list.replaceChildren();
    if (!data.conversations.length) {
      const empty = document.createElement("p");
      empty.className = "empty-inline";
      empty.textContent = "No conversations yet. Start chatting whenever you’re ready.";
      list.append(empty);
      return;
    }
    data.conversations.forEach((conversation) => {
      const link = document.createElement("a");
      link.className = "history-item";
      link.href = `/history?conversation=${conversation.id}`;
      const title = document.createElement("strong");
      title.textContent = `Conversation #${conversation.id}`;
      const time = document.createElement("time");
      time.textContent = dateLabel(conversation.last_activity);
      const countLabel = document.createElement("span");
      countLabel.className = "history-item-count";
      countLabel.textContent = `${conversation.message_count} messages`;
      link.append(title, time, countLabel);
      list.append(link);
    });
    const selected = params.get("conversation");
    if (selected) await openConversation(selected);
  }

  load().catch((error) => {
    list.replaceChildren();
    const message = document.createElement("p");
    message.className = "alert-error";
    message.textContent = error.message;
    list.append(message);
  });
})();
